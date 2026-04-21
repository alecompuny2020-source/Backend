from django.db import models, transaction
import uuid
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from common.managers import EnterpriseUserManager
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.postgres.indexes import GinIndex
from common.services import upload_profile_picture
from django.conf import settings
from common.validators import image_validator, validate_image_mime
from common.choices import ADDRESS_TYPES


class User(AbstractBaseUser, PermissionsMixin):
    """ Core Enterprise Identity Model. """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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

    objects = EnterpriseUserManager()

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
