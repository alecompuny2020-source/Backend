from django.contrib.auth.models import BaseUserManager
from django.db.models import Q
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from phonenumber_field.phonenumber import to_python
from .sender.gateway import NotificationSenderGateway as NotificationGateway


class EnterpriseUserManager(BaseUserManager):
    def create_user(self, email=None, password=None, **extra_fields):
        if not email and not extra_fields.get("phone_number"):
            raise ValueError("Either email or phone number must be set")
        user = self.model(email=email or None, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class EnterpriseOTPandLinkManager:
    """
    Unified manager for OTP and Link Lifecycle: Generation, Dispatching, and Verification.
    Maintains enterprise-grade security audit logs and routing logic.
    """

    @classmethod
    def generate_and_send(cls, identifier: str, token_type: str):
        """
        Generates a new OTP for a user and dispatches it via the best channel.
        """
        from core.models import Otp, User

        phone = to_python(identifier)

        try:
            query = Q(email__iexact=identifier)
            if phone and phone.is_valid():
                query |= Q(phone_number=phone)

            if token_type == Otp.TOKEN_TYPE_REGISTRATION:
                user = User.objects.get(query)
            else:
                user = User.objects.get(query, is_verified=True)

        except User.DoesNotExist:
            return Response(
                {"error": "No active account found with the given credentials."},
                status=status.HTTP_404_NOT_FOUND,
            )

        otp_entry = Otp.generate_new_code(user, token_type)

        success, message = NotificationGateway.dispatch_otp_or_link(otp_entry, identifier)

        if not success:
            return Response(
                {"error": "Notification system error.", "detail": message},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if token_type == Otp.TOKEN_TYPE_REGISTRATION:
            res_msg = "OTP for account activation sent."
        elif token_type == Otp.TOKEN_TYPE_PASSWORD_RESET:
            res_msg = "OTP for password reset sent."
        elif token_type == Otp.TOKEN_TYPE_TRANSACTION_AUTH:
            res_msg = "A verification code for your transaction has been sent."
        elif token_type == Otp.TOKEN_TYPE_ACCOUNT_DELETION:
            res_msg = "Security code for account deletion sent. Proceed with caution."
        else:
            res_msg = "OTP code sent successfully!"

        return Response({"message": res_msg}, status=status.HTTP_200_OK)


    @classmethod
    def verify(cls, identifier: str, code: str, token_type: str):
        """
        Verifies the OTP code, handles expiry, and updates user and otp status.
        """
        from core.models import User, Otp

        error_msg = {"error": "Invalid or expired OTP code."}
        phone = to_python(identifier)

        try:
            # Find user first to ensure precise OTP filtering via UUID
            user = User.objects.get(Q(email__iexact=identifier) | Q(phone_number=phone))

            # Find most recent unused OTP
            otp_entry = Otp.objects.filter(
                user=user,
                token_type=token_type,
                is_used=False
            ).latest("created_at")

        except (User.DoesNotExist, Otp.DoesNotExist):
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)

        if otp_entry.code != code:
            otp_entry.increment_attempts()
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)

        if otp_entry.is_expired:
            otp_entry.is_used = True
            otp_entry.save()
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)

        if token_type == Otp.TOKEN_TYPE_REGISTRATION:
            user.is_verified = True
            user.save()
            final_message = "Account activated successfully."

        elif token_type == Otp.TOKEN_TYPE_PASSWORD_RESET:
            final_message = "OTP verified. Proceed to password change."

        elif token_type == Otp.TOKEN_TYPE_PASSWORD_RESET:
            final_message = "OTP verified. You may now change your password."

        elif token_type == Otp.TOKEN_TYPE_TRANSACTION_AUTH:
            final_message = "Transaction authorized successfully."

        elif token_type == Otp.TOKEN_TYPE_ACCOUNT_DELETION:
            final_message = "Security code confirmed. Proceeding with deletion."

        elif token_type == Otp.TOKEN_TYPE_EMAIL_CHANGE:
            final_message = "Email ownership verified."

        elif token_type == Otp.TOKEN_TYPE_STAFF_INVITATION:
            user.is_verified = True
            user.save(update_fields=["is_verified"])
            final_message = "Staff account activated."

        else:
            final_message = "Login OTP verified."

        otp_entry.is_used = True
        otp_entry.otp_metadata["verified_at"] = str(timezone.now())
        otp_entry.save(update_fields=["is_used", "otp_metadata"])

        return Response({"message": final_message}, status=status.HTTP_200_OK)
