# tasks.py
from celery import shared_task
import logging
from django.contrib.auth import get_user_model
from django.apps import apps

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=10
)
def async_send_registration_otp_task(self, user_id, token_type):
    """
    Background worker execution thread. Generates the OTP record securely
    and dispatches notifications through external network gateways.
    """
    try:
        # 1. Safely resolve your models
        OtpModel = apps.get_model('your_app_name', 'Otp') # Replace 'your_app_name' with your app string
        user = User.objects.get(id=user_id)

        # 2. Invoke your existing Model Classmethod to create and save the secure code
        otp_instance = OtpModel.generate_new_code(user=user, token_type=token_type)

        # 3. Handle your notifications dynamically here via background worker.
        # Example call to your Notification Service:
        # NotificationService.send_sms(user.phone_number, f"Your verification code is {otp_instance.code}")

        # Update delivery status metadata for tracking audits safely
        otp_instance.otp_metadata["delivery_status"] = "sent_via_background_worker"
        otp_instance.save(update_fields=["otp_metadata"])

        logger.info(f"Successfully processed registration OTP task for User ID: {user_id}")

    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found during async task processing.")

    except Exception as exc:
        logger.warning(f"Network error or gateway timeout for User {user_id}. Retrying...")
        raise self.retry(exc=exc)
