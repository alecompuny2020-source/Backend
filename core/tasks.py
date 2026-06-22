# your_django_app/tasks.py
from celery import shared_task
import logging
from django.contrib.auth import get_user_model
from django.apps import apps
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=15  # Wait 15 seconds before retrying external API network drops
)
def async_send_registration_otp_task(self, user_id, token_type):
    """
    Executes entirely outside the HTTP Request/Response loop.
    Generates the tracking record and handles external notification gateways.
    """
    try:
        # Resolve models dynamically to safely prevent circular dependency blocks
        OtpModel = apps.get_model('your_django_app', 'Otp') # 👈 Replace with your exact app directory name
        user = User.objects.get(id=user_id)

        # 1. Execute your model's secure generation method
        otp_instance = OtpModel.generate_new_code(user=user, token_type=token_type)

        # 2. Invoke your existing OTPManager service asynchronously via worker thread
        # We target the identifier based on what profile details are available
        identifier = user.email if user.email else str(user.phone_number)

        logger.info(f"Worker generating verification data for {identifier} [Type: {token_type}]")

        # Capture context and push out notification transmission logs
        # E.g., NotificationService.send_otp(identifier, otp_instance.code)

        otp_instance.otp_metadata["delivery_status"] = "processed_via_celery_worker"
        otp_instance.save(update_fields=["otp_metadata"])

    except User.DoesNotExist:
        logger.error(f"Async processing abandoned. User ID {user_id} missing from database.")
    except Exception as exc:
        logger.warning(f"Gateway or database retry triggered for User {user_id}. Error: {exc}")
        raise self.retry(exc=exc)
