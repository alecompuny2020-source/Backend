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
from common.validators import image_validator, validate_image_mime


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
