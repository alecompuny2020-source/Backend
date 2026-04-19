from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class EnterpriseEmailOrPhoneAuthBackend(ModelBackend):
    """ An Enterprise authentication backend for Email or Phone."""
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)

        try:
            user = User.objects.get(
                Q(email__iexact=username) | Q(phone_number=username)
            )
        except User.DoesNotExist:
            # Runs a dummy check to prevent timing attacks
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            logger.critical(f"Duplicate user found for identifier: {username}")
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
