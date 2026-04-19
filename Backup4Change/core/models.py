import secrets
import string
import uuid
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        PermissionsMixin)
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from utils.choices import (ADDRESS_TYPES, ID_TYPES, OTP_CODE_LENGTH,
                             OTP_EXPIRATION_TIME_MINUTES, TOKEN_TYPE_CHOICES,
                             COMMUNICATION_CHOICES, CURRENCY_CHOICES, LANGUAGE_CHOICES)
from utils.validators import (IDs_scan_validator, image_validator,
                                validate_image_mime, validate_scan_mime)
from utils.services import (upload_profile_picture)

# Create your models here.


class UserManager(BaseUserManager):
    def create_user(self, email=None, password=None, **extra_fields):
        if not email and not extra_fields.get("phone_number"):
            raise ValueError("Either email or phone number must be set")
        user = self.model(email=email or None, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """ Core Enterprise Identity Model. """

    id = models.UUIDField(
        default=uuid.uuid4, editable=False, primary_key=True, db_index=True
    )
    email = models.EmailField(_("Email Address"), unique=True, db_index=True, null=True, blank=True)
    phone_number = PhoneNumberField(
        _("Phone Number"), null=True, unique=True, db_index=True, blank=True
    )
    first_name = models.CharField(_("First Name"), max_length=30, blank=True)
    middle_name = models.CharField(_("Middle Name"), max_length=100, blank=True)
    last_name = models.CharField(_("Last Name"), max_length=100, blank=True)
    is_active = models.BooleanField(_("Active"), default=True)
    is_staff = models.BooleanField(_("Staff Status"), default=False)
    is_default_password = models.BooleanField(
        _("Using Default Password"),
        default=False,
        help_text=_("Flag for staff; forced password change required if True."),
    )
    is_verified = models.BooleanField(
        _("Identity Verified"),
        default=False,
        help_text=_(
            "Designates whether the user has verified their email/phone via OTP."
        ),
    )
    is_profile_complete = models.BooleanField(
        _("Profile Complete"),
        default=False,
        help_text=_("True if the user has filled in all required HR/KYC metadata."),
    )
    profile_picture = models.ImageField(
        _("Profile Picture"),
        upload_to=upload_profile_picture,
        validators=[image_validator, validate_image_mime],
        null=True,
        blank=True,
        help_text=_("User's photo for visual identification on Kiosks and reports."),
    )

    # ENTERPRISE METADATA FOR STATUS LOGIC
    # This JSON field allows the API to store the 'Why' behind a status.
    # {
    #   "verification_method": "SMS_OTP",
    #   "initialized": "SMS_OTP",
    #   "profile_completion_steps": ["next_of_kin", "id_upload"],
    #   "password_reset_history": [{"timestamp": 1712345678, "reason": "Initial Setup"}]
    # }
    status_metadata = models.JSONField(
        _("Status Metadata"),
        default=dict,
        blank=True,
        help_text=_(
            "Detailed audit data for verification and profile completion stages."
        ),
    )

    # this stands as the hire date to employees
    date_joined = models.DateTimeField(_("Date Joined"), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "phone_number"]

    class Meta:
        db_table = "user"
        verbose_name = _("User")
        verbose_name_plural = _("System Users")
        indexes = [
            GinIndex(fields=["status_metadata"], name="status_metadata_gin_idx"),
        ]

        permissions = [
            ("can_register_staff", "Can register a new staff user"),
            ("can_reset_password_other_user", "Can force reset any user's password"),
            ("can_deactivate_user", "Can deactivate any user account (is_active = False)"),
            ("can_toggle_is_staff", "Can change a user's is_staff status"),
            ("can_change_self_password", "Can reset individual password"),
        ]

    # def clean(self):
    #     """Ensure names are not just whitespace and logic is consistent."""
    #     if not self.first_name.strip() or not self.last_name.strip():
    #         raise ValidationError(_("Names cannot be empty or whitespace only."))

    def get_full_name(self):
        """Returns string representation of the user as what he or she filled"""

        names = [self.first_name, self.middle_name, self.last_name]
        full_name = " ".join([n for n in names if n]).strip()
        contact = self.email if self.email else self.phone_number
        return full_name.title() if full_name else contact

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated User details from: {old_data} to: "
                f"{{'email': '{self.email}', 'phone_number': '{self.phone_number}', 'name': '{self.get_full_name()}'}}"
            )
        return f"Created new User account: {self.get_full_name()} ({self.email})"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.profile_picture.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.get_full_name()


class UserAddress(models.Model):
    """
    Supports multiple addresses per user (e.g., Home, Work, Billing).
    Essential for checkout flow and regional tax/shipping calculations.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    address_type = models.CharField(
        _("Address Type"), max_length=20, choices=ADDRESS_TYPES, default="shipping"
    )
    is_default = models.BooleanField(_("Default Address"), default=False)
    street_address = models.TextField(_("Street Address"))
    city = models.CharField(_("City"), max_length=100)
    state_province = models.CharField(_("State/Province"), max_length=100)
    postal_code = models.CharField(_("Postal Code"), max_length=20)
    country = models.CharField(_("Country"), max_length=100)

    class Meta:
        db_table = "user_address"
        verbose_name = _("User Address")
        verbose_name_plural = _("User Addresses")
        unique_together = ("user", "address_type")

    def get_log_message(self, old_data=None):
        if old_data:
            return f"Updated {self.address_type.title()} Address from: {old_data} to: {self.street_address}, {self.city}"
        return f"Added {self.address_type.title()} Address : {self.street_address}, {self.city}"

    def save(self, *args, **kwargs):
        """Helper: Ensure only one default address exists per type for this user."""
        if self.is_default:
            with transaction.atomic():
                UserAddress.objects.filter(
                    user=self.user, address_type=self.address_type
                ).update(is_default=False)
        super().save(*args, **kwargs)


class UserPreference(models.Model):
    """
    Stores user-specific settings for the e-commerce experience,
    including communication channels and marketing opt-ins.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preferences"
    )

    # preference data
    # {
    #   "communication_method": "email",
    #   "preferred_language": "en-us",
    #   "preferred_currency": "TZS",
    #   "preferred_region": "North America",
    #   "marketing_notifications": true
    # }
    preferences = models.JSONField(
        _("Preferences"),
        default=dict,
        help_text=_("Flexible JSON object storing user preferences."),
    )

    class Meta:
        db_table = "user_preference"
        verbose_name = _("User Preference")
        verbose_name_plural = _("User Preferences")
        indexes = [
            GinIndex(fields=["preferences"], name="preferences_gin_idx"),
        ]

    # def clean(self):
    #     """Validate the JSON keys and values before saving."""
    #     lang = self.preferences.get('preferred_language')
    #     curr = self.preferences.get('preferred_currency')
    #
    #     # Validate Language
    #     if lang and lang not in dict(LANGUAGE_CHOICES):
    #         raise ValidationError({'preferences': _("Invalid language code.")})
    #
    #     # Validate Currency
    #     if curr and curr not in dict(CURRENCY_CHOICES):
    #         raise ValidationError({'preferences': _("Unsupported currency.")})
    #
    # def save(self, *args, **kwargs):
    #     self.full_clean() # Force validation on every save
    #     super().save(*args, **kwargs)

    # @property
    # def language_label(self):
    #     """Returns the human-readable name, e.g., 'Kiswahili'"""
    #     lang_code = self.preferences.get('preferred_language', 'en-us')
    #     return dict(LANGUAGE_CHOICES).get(lang_code, 'English')
    #
    # @property
    # def currency_symbol(self):
    #     """Handy for the frontend to know which symbol to show"""
    #     symbols = {'TZS': 'TSh', 'USD': '$', 'CNY': '¥', 'EUR': '€'}
    #     return symbols.get(self.preferences.get('preferred_currency'), '$')

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated User Preferences for {self.user} "
                f"from: {old_data} to: communication {self.communication_method}, "
                f"language {self.preferred_language}, currency {self.preferred_currency}, "
                f"region {self.preferred_region}, marketing {self.marketing_notifications}"
            )
        return (
            f"Created User Preferences for {self.user} "
            f"communication {self.communication_method}, language {self.preferred_language}, "
            f"currency {self.preferred_currency}, region {self.preferred_region}, "
            f"marketing {self.marketing_notifications}"
        )


class Otp(models.Model):
    """Secure Token Logic: Prevents brute-force and validates expiry."""

    TOKEN_TYPE_REGISTRATION = "registration"
    TOKEN_TYPE_LOGIN = "login"
    TOKEN_TYPE_PASSWORD_RESET = "password_reset"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # email = models.EmailField(null=True, blank=True, db_index = True)
    code = models.CharField(_("OTP Code"), max_length=OTP_CODE_LENGTH)
    is_used = models.BooleanField(_("Is Used"), default=False)
    expires_at = models.DateTimeField(_("Expires At"), db_index=True)
    created_at = models.DateTimeField(_("Created At"), default=timezone.now)
    token_type = models.CharField(
        _("Token Type"), max_length=20, choices=TOKEN_TYPE_CHOICES
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


# class UserActivityLog(models.Model):
#     """Tracks every action performed by the authenticated user"""
#
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     activity = models.TextField()
#     metadata = models.JSONField(blank=True, null=True)
#     timestamp = models.DateTimeField(auto_now_add=True)
#     ip_address = models.GenericIPAddressField(null=True)
#
#     class Meta:
#         ordering = ["-timestamp"]
#         db_table = "activity_log"
#         verbose_name = _("User Log")
#         verbose_name_plural = _("User Logs")
#
#     def get_log_message(self, old_data=None):
#         return f"User {self.user.email} performed activity: {self.activity}"
