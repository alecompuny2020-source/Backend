import uuid

# from django.contrib.gis.db import models as coordinates
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.constants import now


class BaseEnterpriseModelMixin(models.Model):
    """Reusable Base Model for Enterprise Apps"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class BaseLookupConfigurationModelMixin(BaseEnterpriseModelMixin):
    """
    Abstract structural base model for all enterprise dynamic configurations.
    Replaces static TextChoices with high-performance real-time relational metadata.
    """

    name = models.CharField(max_length=200, unique=True, verbose_name=_("Name"))
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name=_("Unique Immutable Handle Code"),
        help_text=_(
            "Programmatic slug key used strictly in backend code logic conditions."
        ),
    )
    description = models.TextField(
        blank=True, verbose_name=_("Operational Description/UI Tooltip")
    )
    color_hex = models.CharField(
        max_length=7, default="#7F8C8D", verbose_name=_("Frontend Theme Hex Color")
    )
    sort_order = models.PositiveSmallIntegerField(
        default=0, db_index=True, verbose_name=_("Execution Sequencing Order")
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_("Active State Configuration Visibility"),
    )

    class Meta(BaseEnterpriseModelMixin.Meta):
        abstract = True
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class BaseEnterpriseAuditModelMixin(BaseEnterpriseModelMixin):
    """Abstract base class to provide common audit fields."""

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name="%(app_label)s_%(class)s_created",
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_updates",
    )

    created_on = models.DateTimeField(_("Created On"), db_index=True, default=now)

    updated_on = models.DateTimeField(
        _("Updated On"), auto_now=False, db_index=True, null=True
    )

    class Meta(BaseEnterpriseModelMixin.Meta):
        abstract = True

    def save(self, *args, **kwargs):
        if not hasattr(self, "created_by") or self.created_by is None:

            from core.models import User

            system_email = "system@enterprise.local"

            system_user, _ = User.objects.get_or_create(
                email=system_email,
                defaults={
                    "is_active": False,  # Hawezi kulogin
                    "first_name": "SYSTEM",
                    "last_name": "BOT",
                },
            )
            self.created_by = system_user

        super().save(*args, **kwargs)


class BaseAddressModelMixin(BaseEnterpriseModelMixin):
    """Reusable Base Address Model throughout the Enterprise"""

    country = models.CharField(_("Country"), max_length=100)
    region = models.CharField(max_length=100, db_index=True)
    district = models.CharField(max_length=100, db_index=True)
    ward = models.CharField(max_length=100)
    postcode = models.CharField(max_length=5, db_index=True)
    # gps_coordinates = coordinates.PointField(_("GPS Coordinates"), geography = True, null = True, blank = True, srid = 4326)

    # DYNAMIC FIELD (For Granularity)
    # Stores: street_name, plot_no, block_no, house_no, village, hamlet, landmark, etc.
    address_metadata = models.JSONField(default=dict, blank=True)

    class Meta(BaseEnterpriseModelMixin.Meta):
        abstract = True


# class ActionTrackingBaseModelMixin(models.Model):
#     """
#     Abstract base class for multi-stage workflow tracking.
#     Ideal for items requiring verification and formal registration.
#     """
#
#     initiated_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.RESTRICT,
#         related_name="%(app_label)s_%(class)s_initiated",
#     )
#     initiated_at = models.DateTimeField(
#         _("Initiated At"), default=now, db_index=True
#     )
#
#     verified_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="%(app_label)s_%(class)s_verified",
#     )
#     verified_at = models.DateTimeField(_("Verified At"), null=True, blank=True)
#
#     registered_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="%(app_label)s_%(class)s_registered",
#     )
#     registered_at = models.DateTimeField(_("Registered At"), null=True, blank=True)
#
#     class Meta:
#         abstract = True
#
#
# class TrashableModelMixin(models.Model):
#     """
#     Abstract Base Class for Soft-Delete functionality.
#     Ensures data integrity by preventing permanent loss of records.
#     """
#
#     is_deleted = models.BooleanField(
#         _("Is Deleted"),
#         default=False,
#         db_index=True,
#         help_text=_("Toggle to move this record to the Trash UI."),
#     )
#     deleted_at = models.DateTimeField(_("Deleted At"), null=True, blank=True)
#
#     # Blueprint for trash_metadata:
#     # {
#     #   "deleted_by_id": "UUID",
#     #   "deletion_reason": "Mistyped batch ID",
#     #   "previous_status": "ACTIVE",
#     #   "ip_address": "192.168.1.1",
#     #   "auto_purge_date": "2026-03-24"
#     # }
#     trash_metadata = models.JSONField(
#         _("Trash Metadata"),
#         default=dict,
#         blank=True,
#         help_text=_("Audit data regarding who deleted the record and why."),
#     )
#
#     class Meta:
#         abstract = True
#
#     def soft_delete(self, user_id=None, reason=None):
#         """
#         Moves the item to the Trash without removing it from the DB.
#         """
#         self.is_deleted = True
#         self.deleted_at = timezone.now()
#
#         self.trash_metadata.update(
#             {
#                 "deleted_by_id": str(user_id) if user_id else None,
#                 "deletion_reason": reason,
#                 "auto_purge_date": (self.deleted_at + timedelta(days=30)).strftime(
#                     "%Y-%m-%d"
#                 ),
#             }
#         )
#         self.save()
#
#     def restore(self):
#         """
#         Restores the record to the active dataset.
#         """
#         self.is_deleted = False
#         self.deleted_at = None
#         # Keep the history of who deleted it in metadata for audit purposes
#         self.trash_metadata["last_restored_at"] = timezone.now().isoformat()
#         self.save()
#
#     @property
#     def days_until_purge(self):
#         """Calculates how long until the record is permanently deleted."""
#         if self.deleted_at:
#             purge_date = self.deleted_at + timedelta(days=30)
#             remaining = purge_date - timezone.now()
#             return max(0, remaining.days)
#         return None
#
#
# class GeneralAuditFieldsMixin(serializers.ModelSerializer):
#     """ Enterprise mixin to handle ownership and YES/NO formatting. """
#     created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
#     updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
#
#     def to_representation(self, instance):
#         """Automatically converts booleans to YES/NO for any field starting with 'is_'"""
#         data = super().to_representation(instance)
#         for field, value in data.items():
#             if field.startswith('is_') and isinstance(value, bool):
#                 data[field] = "YES" if value else "NO"
#         return data
#
#     def create(self, validated_data):
#         validated_data['created_by'] = self.context['request'].user
#         return super().create(validated_data)
#
#     def update(self, instance, validated_data):
#         validated_data['updated_by'] = self.context['request'].user
#         validated_data['updated_on'] = now_iso
#         return super().update(instance, validated_data)
