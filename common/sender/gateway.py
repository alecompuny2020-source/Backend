from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from .sms import SMSSenderService
from .emails import EmailSenderService

import random
from .sms import SMSSenderService
from .email import EmailSenderService

class NotificationsSenderGateway:
    """
    Central logic engine to determine and dispatch notifications
    via the most appropriate channel (Email or SMS).
    """

    @classmethod
    def dispatch_otp(cls, otp_entry):
        """
        Determines the delivery method for an OTP and dispatches it.
        Follows priority: User Preference -> Profile Availability -> Random Selection.
        """
        user = otp_entry.user
        method = cls._resolve_delivery_method(user)

        if method == "email":
            return EmailSenderService.send_otp(otp_entry)

        return SMSSenderService.send_otp(otp_entry)

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

    @staticmethod
    def _is_method_available(user, method):
        """Helper to verify if the preferred method actually has data in profile."""
        if method == "email":
            return bool(user.email)
        if method == "phone":
            return bool(user.phone_number)
        return False

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
