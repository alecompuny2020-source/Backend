from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Q
from django.db import transaction
from django.conf import settings
from django.shortcuts import render
from phonenumber_field.phonenumber import to_python
from rest_framework import generics, permissions, status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.utils.translation import gettext_lazy as _
from utils.services import (
    generate_new_otp, verify_otp, send_onboarding_notification, generate_secure_password,
    send_otp_email, send_forgot_password_link_email, mask_email
)
from django.utils import timezone

from .models import Otp
from lrh.models import EmployeeRegistrationHistory
from .serializers import (ConfirmPasswordResetSerializer, UserAddressSerializer,
                          ConfirmRegistrationSerializer, UserPreferenceSerializer,
                          ForgotPasswordConfirmSerializer, OnboardConfirmSerializer,
                          LoginConfirmOTPSerializer, RequestLoginOTPSerializer,
                          RegistrationSerializer, ProfilePictureSerializer,
                          RequestForgotPasswordSerializer, StaffOnboardingSerializer,
                          RequestOTPSerializer, UserTokenObtainPairSerializer,
                          RequestOnboardingLinkSerializer, CompleteProfileSerializer)

# Create your views here.


User = get_user_model()


class AuthViewSet(viewsets.GenericViewSet):

    """ A view that Consolidated authentication flows (registration, login, password reset, and forgot password)"""

    permission_classes = [permissions.AllowAny]
    queryset = User.objects.all()

    @action(detail=False, methods=["post"], serializer_class=RegistrationSerializer)
    def initiate_registration(self, request):
        """Attains self user registration"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()

            customer_group, created = Group.objects.filter(
                Q(name="Customer"),
            ).get_or_create(name="Customer")
            user.groups.add(customer_group)

        return Response(_("Registration success. OTP sent for verification."))


    @action(detail = False, methods=['post'], serializer_class = ConfirmRegistrationSerializer)
    def confirm_registration(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 'identifier' is used instead of 'email or phone number since identifier may carry one of the two'
        identifier = serializer.validated_data["identifier"]
        code = serializer.validated_data["OTP"]
        token_type = Otp.TOKEN_TYPE_REGISTRATION
        return verify_otp(identifier, code, token_type)


    @action(detail = False, methods=['post'], serializer_class = RequestLoginOTPSerializer)
    def initiate_login(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data["identifier"]
        password = serializer.validated_data["password"]
        phone_number = to_python(identifier)

        # Lookup user by email or phone number
        try:
            user = User.objects.get(
                Q(email__iexact=identifier) | Q(phone_number=phone_number)
            )
        except User.DoesNotExist:
            return Response(
                {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )

        otp_entry = Otp.generate_new_code(user, Otp.TOKEN_TYPE_LOGIN)

        # Logic to decide notification channel
        if user.email and "@" in identifier:
            success, message = send_otp_email(otp_entry)
        else:
            # Trigger SMS if phone number was used or email is missing
            # success, message = send_otp_sms(otp_entry)
            success, message = send_otp_email(otp_entry)

        if success:
            return Response(_("Login OTP sent successfully."))

        return Response({"error": message}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


    @action(detail = False, methods=['post'], serializer_class = LoginConfirmOTPSerializer)
    def confirm_login(self, request):
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception = True)

        identifier = serializer.validated_data["identifier"]
        code = serializer.validated_data["OTP"]

        # 1. Verify the OTP
        otp_response = verify_otp(identifier, code, Otp.TOKEN_TYPE_LOGIN)

        if otp_response.status_code == status.HTTP_200_OK:
            phone_number = to_python(identifier)
            user = User.objects.get(
                Q(email__iexact=identifier) | Q(phone_number=phone_number)
            )

            # update_last_login(None, user)

            # 2. Issue tokens using your custom Base64-encoding serializer
            token_serializer = UserTokenObtainPairSerializer()
            refresh = token_serializer.get_token(user)

            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user_data": token_serializer.get_user_data(user),
                },
                status=status.HTTP_200_OK,
            )

        return otp_response

    def _handle_otp_request(self, request, token_type):
        """Generic method for requesting various OTP types."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data["identifier"]

        if token_type:
            return generate_new_otp(identifier, token_type)
        return Response(
            {"error": "Invalid token type."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=False, methods=["post"], serializer_class=RequestOTPSerializer)
    def request_registration_otp(self, request):
        return self._handle_otp_request(request, Otp.TOKEN_TYPE_REGISTRATION)

    @action(detail=False, methods=["post"], serializer_class=RequestOTPSerializer)
    def request_login_otp(self, request):
        return self._handle_otp_request(request, Otp.TOKEN_TYPE_LOGIN)

    @action(detail=False, methods=["post"], serializer_class=RequestOTPSerializer,
            permission_classes=[permissions.IsAuthenticated])
    def request_password_reset_otp(self, request):
        return self._handle_otp_request(request, Otp.TOKEN_TYPE_PASSWORD_RESET)

    @action(detail=False, methods=["post"], serializer_class=RequestOnboardingLinkSerializer)
    def request_onboarding_link(self, request):
        """Action to request the setup link."""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        new_raw_password = generate_secure_password()
        initiator = str(request.user) if request.user.is_authenticated else "SYSTEM"

        success, message = send_onboarding_notification(user, raw_password = new_raw_password)
        if not success:
            raise serializers.ValidationError({"error": _("Failed to send link."), "details": message})

        metadata = user.status_metadata or {}

        onboard_history = metadata.get("onboarding_history", [])
        if isinstance(metadata.get("onboarding"), dict):
            onboard_history.append(metadata.pop("onboarding"))

        onboard_history.append({
            "request_by": initiator,
            "requested_at": timezone.now().isoformat(),
            "device_ip_address": request.META.get("REMOTE_ADDR") if request else None,
            "method": "Email" if user.email else "SMS",
            "notification_status": "SENT",
        })

        history = metadata.get("verification_history", [])
        history.append({
            "event": "Onboarding link sent",
            "timestamp": timezone.now().isoformat(),
            "by": initiator
        })

        metadata["verification_history"] = history
        metadata["onboarding_history"] = onboard_history

        user.status_metadata = metadata
        user.save(update_fields=['status_metadata'])

        return Response({"message": _("Onboarding link has been resent successfully.")})

    @action(detail=False, methods=["post"], serializer_class=ConfirmPasswordResetSerializer,
            permission_classes=[permissions.IsAuthenticated])
    def confirm_password_reset(self, request):
        """Password reset method that verify OTP for password reset and set a new Password"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data["identifier"]
        code = serializer.validated_data["OTP"]
        new_password = serializer.validated_data["new_password"]

        otp_response = verify_otp(identifier, code, Otp.TOKEN_TYPE_PASSWORD_RESET)
        phone = to_python(identifier)

        if otp_response.status_code == status.HTTP_200_OK:
            try:
                user = User.objects.get(
                    Q(email__iexact=identifier) | Q(phone_number=phone)
                )
                user.set_password(new_password)
                user.is_default_password = False
                user.save()
                return Response(
                    {"message": "Password reset successful."}, status=status.HTTP_200_OK
                )
            except User.DoesNotExist:
                return Response(
                    {"error": "No active account with the given credentials."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        return otp_response

    @action(detail = False, methods = ['post'], serializer_class = RequestForgotPasswordSerializer, permission_classes = [permissions.AllowAny])
    def initiate_forgot_password(self, request):
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception = True)

        identifier = serializer.validated_data["identifier"]
        user = User.objects.get(Q(email__iexact=identifier))

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        frontend_base = settings.FRONTEND_URL.rstrip("/")
        reset_link = f"{frontend_base}/account/confirm-password-reset/{uid}/{token}/"

        success, message = send_forgot_password_link_email(user, reset_link)

        if success:
            masked = mask_email(user.email)
            return Response(
                {"detail": f"Password reset link sent to {masked}."},
                status=status.HTTP_200_OK,
            )
        else:

            return Response(
                {"error": "Unable to deliver reset email.", "detail": message},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    @action(detail = False, serializer_class = ForgotPasswordConfirmSerializer, methods = ['post'])
    def confirm_forgot_password(self, request):
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception = True)

        uidb64 = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(Q(pk=uid))
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):

            user.set_password(new_password)
            user.save()

            return Response(
                {"detail": "Your password was updated. You can now sign in."},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": "Invalid or Expired link. Please request a new one."},
            status = status.HTTP_400_BAD_REQUEST,
        )

    @action(detail = False, methods = ["get", "post", "put", "patch", "delete"], serializer_class = ProfilePictureSerializer,
        permission_classes = [permissions.IsAuthenticated])
    def user_profile_picture(self, request):
        """ Allow authenticated users to retrieve, upload or update their profile picture."""

        user = request.user

        if request.method.lower() == "get":
            serializer = self.get_serializer(instance=user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method.lower() in ["post", "put", "patch"]:
            had_picture = bool(user.profile_picture)
            is_partial = request.method.lower() in ["post", "patch"]

            serializer = self.get_serializer(instance=user, data=request.data, partial=is_partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            message = "Profile picture updated successfully." if had_picture else "Profile picture uploaded successfully."
            return Response({"detail": message}, status=status.HTTP_200_OK)

        elif request.method.lower() == "delete":
            if user.profile_picture:
                user.profile_picture.delete(save=False)
                user.profile_picture = None
                user.save()
                return Response({"detail": "Profile picture deleted successfully."},
                                status=status.HTTP_200_OK)
            return Response({"error": "No profile picture to delete."},
                            status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["get", "post", "put", "patch", "delete"],
        serializer_class=UserAddressSerializer,
        permission_classes=[permissions.IsAuthenticated])
    def user_addresses(self, request):
        """ Allow authenticated users to Manage their addresses"""

        user = request.user

        if request.method.lower() == "get":
            addresses = user.addresses.all()
            serializer = self.get_serializer(addresses, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method.lower() == "post":
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user)
            return Response({"detail": "Address added successfully."}, status=status.HTTP_201_CREATED)

        elif request.method.lower() in ["put", "patch"]:
            address_id = request.data.get("id")
            try:
                address = user.addresses.get(id=address_id)
            except UserAddress.DoesNotExist:
                return Response({"error": "Address not found."}, status=status.HTTP_404_NOT_FOUND)

            serializer = self.get_serializer(address, data=request.data, partial=(request.method.lower()=="patch"))
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"detail": "Address updated successfully."}, status=status.HTTP_200_OK)

        elif request.method.lower() == "delete":
            address_id = request.data.get("id")
            try:
                address = user.addresses.get(id=address_id)
                address.delete()
                return Response({"detail": "Address deleted successfully."}, status=status.HTTP_200_OK)
            except UserAddress.DoesNotExist:
                return Response({"error": "Address not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["get", "post", "put", "patch", "delete"],
        serializer_class=UserPreferenceSerializer,
        permission_classes=[permissions.IsAuthenticated])
    def user_preferences(self, request):
        """ Allow authenticated users to Manage their preferences """

        user = request.user

        if request.method.lower() == "get":
            try:
                serializer = self.get_serializer(instance=user.preferences)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except UserPreference.DoesNotExist:
                return Response({"error": "Preferences not set."}, status=status.HTTP_404_NOT_FOUND)

        elif request.method.lower() == "post":
            if hasattr(user, "preferences"):
                return Response({"error": "Preference already exist."},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user)
            return Response({"detail": "Preferences created successfully."}, status=status.HTTP_201_CREATED)

        elif request.method.lower() in ["put", "patch"]:
            try:
                preferences_obj = user.preferences
            except UserPreference.DoesNotExist:
                return Response({"error": "Preferences not found."}, status=status.HTTP_404_NOT_FOUND)

            serializer = self.get_serializer(preferences_obj, data=request.data,
                                             partial=(request.method.lower() == "patch"))
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"detail": "Preferences updated successfully."}, status=status.HTTP_200_OK)

        elif request.method.lower() == "delete":
            try:
                preferences_obj = user.preferences
                preferences_obj.delete()
                return Response({"detail": "Preferences deleted successfully."}, status=status.HTTP_200_OK)
            except UserPreference.DoesNotExist:
                return Response({"error": "Preferences not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], serializer_class=StaffOnboardingSerializer, permission_classes=[permissions.IsAdminUser])
    def initiate_staff_onboarding(self, request):
        """ Action to initiate the onboarding process for a new staff member."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        error = _("An error occurred during onboarding.")

        try:
            employee = serializer.save()
            return Response({
                "message": _("Staff onboarding initiated successfully."),
                "data": {
                    # "employee_id": employee.id,
                    "employee_number": employee.employee_number,
                    "email": employee.user.email if employee.user.email else None,
                    "phone_number": str(employee.user.phone_number) if employee.user.phone_number else None,
                    "department": employee.department.name,
                }
            }, status=status.HTTP_201_CREATED)

        except serializers.ValidationError as e:
            return Response({
                "error": error,
                "details": e.detail
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "error": error,
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=False, methods=['post'], serializer_class=OnboardConfirmSerializer)
    def confirm_staff_onboarding(self, request):
        """
        Confirms the staff onboarding link, sets new password,
        and updates the user's status flags.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uidb64 = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({
                "error": _("Invalid user identifier. Please check the link or contact support.")
            })

        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError({
                "error": _("The setup link has expired or is invalid. Please request a new one.")
            })

        with transaction.atomic():
            user.set_password(new_password)
            user.is_default_password = False
            user.is_verified = True
            user.is_active = True

            metadata = user.status_metadata or {}
            now_iso = timezone.now().isoformat()
            user_str = str(user)

            verification_history = metadata.get("verification_history", [])
            verification_history.append({
                "event": "Account activated",
                "timestamp": now_iso,
                "by": user_str
            })
            metadata["verification_history"] = verification_history

            metadata["security_log"] = {
                "last_password_change": now_iso,
                "is_forced_reset_pending": False
            }

            reset_history = metadata.get("password_reset_history", [])
            reset_history.append({
                "timestamp": int(timezone.now().timestamp()),
                "reason": "Initial Setup/Onboarding",
                "new_password_set": True
            })
            metadata["password_reset_history"] = reset_history

            user.status_metadata = metadata
            user.save()

            if hasattr(user, 'employee_profile'):
                emp = user.employee_profile
                EmployeeRegistrationHistory.objects.update_or_create(
                    employee=emp,
                    status="VERIFIED",
                    verified_by=user,
                    verified_at=now_iso,
                    remarks=_("Onboarding confirmed via security token.")
                )

        return Response({
            "message": _("Account setup complete. You can now sign in to the dashboard."),
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['put'], serializer_class = CompleteProfileSerializer)
    def complete_profile(self, request, pk=None):
        """ Handles profile completion logics """
        instance = self.get_object()

        serializer = self.get_serializer(instance, data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Profile completed successfully.",
                    "is_profile_complete": instance.is_profile_complete
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
