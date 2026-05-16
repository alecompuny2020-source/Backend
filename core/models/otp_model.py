from django.db import models
from common.mixins import BaseEnterpriseModelMixin
import secrets
import string
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from common.choices import (OTP_CODE_LENGTH, TOKEN_TYPE_CHOICES, OTP_EXPIRATION_TIME_MINUTES)



class Otp(BaseEnterpriseModelMixin):
    """Secure Token Logic: Prevents brute-force and validates expiry."""

    TOKEN_TYPE_REGISTRATION = "registration"
    TOKEN_TYPE_LOGIN = "login"
    TOKEN_TYPE_PASSWORD_RESET = "password_reset"
    TOKEN_TYPE_TRANSACTION_AUTH = "transaction_auth"
    TOKEN_TYPE_EMAIL_CHANGE = "email_change"
    TOKEN_TYPE_PHONE_VERIFICATION = "phone_verification"
    TOKEN_TYPE_2FA_ENABLE = "2fa_enable"
    TOKEN_TYPE_ACCOUNT_DELETION = "account_deletion"
    TOKEN_TYPE_STAFF_INVITATION = "staff_invitation"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(_("OTP Code"), max_length=OTP_CODE_LENGTH)
    is_used = models.BooleanField(_("Is Used"), default=False)
    expires_at = models.DateTimeField(_("Expires At"), db_index=True)
    created_at = models.DateTimeField(_("Created At"), default=timezone.now)
    token_type = models.CharField(
        _("Token Type"), max_length=20, choices=TOKEN_TYPE_CHOICES
    )
    is_link_based = models.BooleanField(
        _("Is Link Based"),
        default=False,
        help_text=_("Indicates if this record represents an email-based secure link.")
    )
    # --- Enterprise Metadata (The 'Sweet' Logic) ---
    # Blueprint:
    # {
    #   "attempt_count": 0,
    #   "ip_address": "192.168.1.1",
    #   "user_agent": "Mozilla/5.0...",
    #   "delivery_status": "sent_via_sms"
    # }
    otp_metadata = models.JSONField(
        _("OTP Metadata"),
        default=dict,
        blank=True,
        help_text=_(
            "Stores security audit data like attempt counts and delivery logs."
        ),
    )

    class Meta:
        db_table = "otp"
        verbose_name = _("OTP Token")
        verbose_name_plural = _("OTP Tokens")
        ordering = ["-created_at"]

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def increment_attempts(self):
        """Tracks failed attempts to trigger account lockout if necessary."""
        count = self.otp_metadata.get("attempt_count", 0)
        self.otp_metadata["attempt_count"] = count + 1
        self.save(update_fields=["otp_metadata"])

    @staticmethod
    def _generate_secure_code(length=OTP_CODE_LENGTH):
        """Generates a cryptographically secure random numeric code."""
        return "".join(secrets.choice(string.digits) for _ in range(length))

    @classmethod
    def generate_new_code(cls, user, token_type):
        """
        Generates a secure code, calculates expiry time,
        creates a new OTP entry and wipes previous unused tokens for the user.
        """
        cls.objects.filter(user=user, token_type=token_type, is_used=False).delete()
        expiry = timezone.now() + timedelta(minutes=OTP_EXPIRATION_TIME_MINUTES)
        code = cls._generate_secure_code()
        return cls.objects.create(
            user=user,
            code=code,
            token_type=token_type,
            expires_at=expiry,
            otp_metadata={"attempt_count": 0, "generated_at": str(timezone.now())},
        )

    def get_log_message(self, old_data=None):
        if old_data:
            return f"Updated OTP {self.token_type} for {self.user.email}"
        return f"Generated new ({self.token_type}) OTP for {self.user.email}"
