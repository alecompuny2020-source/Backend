import africastalking
from django.conf import settings
from common.exceptions import handle_sms_exception


class SMSSenderService:
    """Handles all outgoing SMS communications via Africa's Talking API."""

    @staticmethod
    def _dispatch_sms(message, recipients):
        """Internal helper to initialize client and send SMS with consistent handling."""
        try:
            africastalking.initialize(settings.AT_USERNAME, settings.AT_API_KEY)
            sms = africastalking.SMS

            # AT expects a list of recipients
            response = sms.send(message, recipients)

            # Check the status of the first recipient (since we usually send to one)
            status = response['SMSMessageData']['Recipients'][0]['status']
            if status in ['Success', 'Sent']:
                return True, "SMS sent successfully."

            return False, f"SMS Gateway returned status: {status}"
        except Exception as e:
            return SMSExceptionHandler.handle(e)

    @classmethod
    def send_otp(cls, otp_entry):
        """Sends a verification code to a user's phone number."""
        message = (
            f"Daz Electronics: Namba yako ya siri ya {otp_entry.token_type} ni {otp_entry.code}. "
            f"Valid for {settings.OTP_EXPIRATION_TIME // 60} minutes."
        )
        return cls._dispatch_sms(message, [str(otp_entry.phone_number)])

    @classmethod
    def send_staff_credentials(cls, phone_number, password, completion_link):
        """Sends onboarding login details to new staff members."""
        message = (
            f"Karibu! Your staff account is ready.\n"
            f"User: {phone_number}\nPass: {password}\n"
            f"Login: {completion_link}"
        )
        return cls._dispatch_sms(message, [str(phone_number)])
