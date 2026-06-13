# signals.py
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .tasks import async_send_registration_otp_task

User = get_user_model()

@receiver(post_save, sender=User)
def on_user_registration_trigger(sender, instance, created, **kwargs):
    """
    Listens directly to the database layer. Fires automatically right after
    your view calls `serializer.save()`.
    """
    if created:
        # Enforce transaction boundary isolation using on_commit.
        # This prevents the Celery task from executing until the database transaction is closed out completely.
        # Note: We pass strings for token types to prevent model circular dependencies.
        token_type = "REGISTRATION" # Adjust based on your TokenType choices setup

        transaction.on_commit(
            lambda: async_send_registration_otp_task.delay(
                user_id=instance.id,
                token_type=token_type
            )
        )
