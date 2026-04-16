import africastalking
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class SMSSenderService:
    """Handles all outgoing SMS communications via Africa's Talking API."""

    @staticmethod
    def _get_client():
        """Initializes the Africa's Talking SMS client."""
        africastalking.initialize(settings.AT_USERNAME, settings.AT_API_KEY)
        return africastalking.SMS

    @classmethod
    def send_otp(cls, otp_entry):
        """Sends a verification code to a user's phone number."""
        try:
            sms = cls._get_client()
            message = (
                f"Your {otp_entry.token_type} verification code is: {otp_entry.code}. "
                f"It is valid for {settings.OTP_EXPIRATION_TIME // 60} minutes."
            )
            response = sms.send(message, [str(otp_entry.phone_number)])
            logger.info(f"OTP SMS sent: {response}")
            return True, "SMS sent successfully."
        except Exception as e:
            logger.error(f"SMS OTP failure: {e}")
            return False, "Failed to send SMS code."

    @classmethod
    def send_staff_credentials(cls, phone_number, password, completion_link):
        """Sends onboarding login details to new staff members."""
        try:
            sms = cls._get_client()
            message = (
                f"Karibu! Your staff account is ready. "
                f"Username: {phone_number} Password: {password}. "
                f"Login here: {completion_link}"
            )
            sms.send(message, [str(phone_number)])
            return True, "Staff credentials sent via SMS."
        except Exception as e:
            logger.error(f"Staff SMS failure: {e}")
            return False, "Failed to send staff notification."
