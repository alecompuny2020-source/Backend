import random
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from .sms import SMSSenderService
from .email import EmailSenderService


class NotificationSenderGateway:
    """
    Determines the delivery method for an OTP or link and dispatches it.
    Follows priority: User Preference -> Profile Availability -> Random Selection.
    """

    @classmethod
    def dispatch_otp_or_link(cls, otp_entry, identifier = None, credential = None):
        """
        Primary Router: Checks the token type and routes to the correct
        specialized class method.
        """
        user = otp_entry.user
        token_type = otp_entry.token_type

        if token_type == "password_reset":
            return cls.dispatch_forgot_password_link(user, identifier)

        if token_type == "staff_invitation":
            return cls.dispatch_onboarding(user, getattr(user, credential))

        method = cls._resolve_delivery_method(user)
        if method == "email":
            return EmailSenderService.send_otp(otp_entry)

        return SMSSenderService.send_otp(otp_entry)

    @staticmethod
    def _is_method_available(user, method):
        """Helper to verify if the preferred method actually has data in profile."""
        if method == "email":
            return bool(user.email)
        if method == "phone":
            return bool(user.phone_number)
        return False

    @staticmethod
    def _resolve_delivery_method(user):
        """
        Logic to choose between 'email' or 'sms'.
        1. Check UserPreference model.
        2. Check if only one contact method exists.
        3. Randomly select if both exist.
        """

        if hasattr(user, 'preferences'):
            pref_method = user.preferences.preferences.get("communication_method")
            if pref_method in ["email", "phone"] and cls._is_method_available(user, pref_method):
                return "email" if pref_method == "email" else "sms"

        has_email = bool(user.email)
        has_phone = bool(user.phone_number)

        if has_email and has_phone:
            return random.choice(["email", "sms"])

        if has_email:
            return "email"

        return "sms"


    @classmethod
    def dispatch_forgot_password_link(cls, user, provided_identifier):
        """
        Specialized logic for Forgot Password (The 3 Conditions):
        1. If both exist, use the one NOT provided (Security Swap).
        2. If both exist and preference is set, use preference.
        3. If only one exists, use that one.
        """
        has_email = bool(user.email)
        has_phone = bool(user.phone_number)
        provided_is_email = "@" in provided_identifier

        # Condition 3: Check Preference first (Highest Priority)
        if hasattr(user, 'preferences') and has_email and has_phone:
            pref = user.preferences.preferences.get("communication_method")
            if pref in ["email", "phone"]:
                return cls._execute_reset(user, "email" if pref == "email" else "sms")

        # Condition 2: Both exist - Security Swap (Use the 'other' one)
        if has_email and has_phone:
            # If they gave email, send to phone. If they gave phone, send to email.
            target = "sms" if provided_is_email else "email"
            return cls._execute_reset(user, target)

        # Condition 1: Only one exists
        target = "email" if has_email else "sms"
        return cls._execute_reset(user, target)

    @classmethod
    def _execute_reset(cls, user, method):
        """Internal helper to trigger the specific Service for password forgot."""

        from common.managers import EnterpriseOTPandLinkManager as OTPManager
        from core.models import Otp, User

        if method == "email":
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            link = f"{settings.FRONTEND_URL}/confirm-forgot-password/{uid}/{token}/"
            return EmailSenderService.send_forgot_password_link(user, link)

        otp_entry = OTPManager.generate_and_send(
            identifier=str(user.phone_number),
            token_type=Otp.TOKEN_TYPE_PASSWORD_RESET
        )
        return SMSSenderService.send_otp(otp_entry)

    @staticmethod
    def dispatch_password_reset(user, reset_link):
        """Dispatches password reset link primarily via Email."""
        if user.email:
            return EmailSenderService.send_password_reset(user, reset_link)
        return False, "Email address required for password reset."

    @classmethod
    def dispatch_onboarding(cls, user, raw_password):
        """Determines whether to notify a new staff via Email or SMS based on availability."""
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        completion_link = f"{settings.FRONTEND_URL.rstrip('/')}/setup-account/{uid}/{token}/"

        if user.email:

            name = user.get_full_name() or "Team Member"
            return EmailSenderService.send_staff_onboarding(user, raw_password, completion_link, name)

        if user.phone_number:
            return SMSSenderService.send_staff_credentials(user.phone_number, raw_password, completion_link)

        return False, "No valid contact method (Email/Phone) found for this user."
