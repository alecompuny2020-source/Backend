import json
import threading

from django.conf import settings
from django.db import models, connections
from django.forms.models import model_to_dict
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, viewsets
from helpers.choices import now_iso, now

_user = threading.local()


class FarmAuditBaseModelMixin(models.Model):
    """ Abstract base class to provide common audit fields."""

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name="%(app_label)s_%(class)s_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_updates",
    )

    created_on = models.DateTimeField(
        _("Created On"), db_index=True, default=now
    )

    updated_on = models.DateTimeField(
        _("Updated On"), auto_now=True, db_index=True, null=True
    )

    class Meta:
        abstract = True


class ActionTrackingBaseModelMixin(models.Model):
    """
    Abstract base class for multi-stage workflow tracking.
    Ideal for items requiring verification and formal registration.
    """

    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name="%(app_label)s_%(class)s_initiated",
    )
    initiated_at = models.DateTimeField(
        _("Initiated At"), default=now, db_index=True
    )

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_verified",
    )
    verified_at = models.DateTimeField(_("Verified At"), null=True, blank=True)

    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_registered",
    )
    registered_at = models.DateTimeField(_("Registered At"), null=True, blank=True)

    class Meta:
        abstract = True


class TrashableModelMixin(models.Model):
    """
    Abstract Base Class for Soft-Delete functionality.
    Ensures data integrity by preventing permanent loss of records.
    """

    is_deleted = models.BooleanField(
        _("Is Deleted"),
        default=False,
        db_index=True,
        help_text=_("Toggle to move this record to the Trash UI."),
    )
    deleted_at = models.DateTimeField(_("Deleted At"), null=True, blank=True)

    # Blueprint for trash_metadata:
    # {
    #   "deleted_by_id": "UUID",
    #   "deletion_reason": "Mistyped batch ID",
    #   "previous_status": "ACTIVE",
    #   "ip_address": "192.168.1.1",
    #   "auto_purge_date": "2026-03-24"
    # }
    trash_metadata = models.JSONField(
        _("Trash Metadata"),
        default=dict,
        blank=True,
        help_text=_("Audit data regarding who deleted the record and why."),
    )

    class Meta:
        abstract = True

    def soft_delete(self, user_id=None, reason=None):
        """
        Moves the item to the Trash without removing it from the DB.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()

        self.trash_metadata.update(
            {
                "deleted_by_id": str(user_id) if user_id else None,
                "deletion_reason": reason,
                "auto_purge_date": (self.deleted_at + timedelta(days=30)).strftime(
                    "%Y-%m-%d"
                ),
            }
        )
        self.save()

    def restore(self):
        """
        Restores the record to the active dataset.
        """
        self.is_deleted = False
        self.deleted_at = None
        # Keep the history of who deleted it in metadata for audit purposes
        self.trash_metadata["last_restored_at"] = timezone.now().isoformat()
        self.save()

    @property
    def days_until_purge(self):
        """Calculates how long until the record is permanently deleted."""
        if self.deleted_at:
            purge_date = self.deleted_at + timedelta(days=30)
            remaining = purge_date - timezone.now()
            return max(0, remaining.days)
        return None


class GeneralAuditFieldsMixin(serializers.ModelSerializer):
    """ Enterprise mixin to handle ownership and YES/NO formatting. """
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)

    def to_representation(self, instance):
        """Automatically converts booleans to YES/NO for any field starting with 'is_'"""
        data = super().to_representation(instance)
        for field, value in data.items():
            if field.startswith('is_') and isinstance(value, bool):
                data[field] = "YES" if value else "NO"
        return data

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        validated_data['updated_on'] = now_iso
        return super().update(instance, validated_data)


class BaseEnterpriseViewSetMixin(viewsets.ModelViewSet):
    """
    A base ViewSet to handle shared configuration and consistent success messages.
    """
    pagination_class = GenericPaginator
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering = ['-id'] # Solves the UnorderedObjectListWarning globally

    def get_success_message(self, action_name):
        messages = {
            'create': "Record created successfully",
            'update': "Record updated successfully",
            'destroy': "Record deleted successfully"
        }
        return messages.get(action_name, "Action successful")

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({"message": self.get_success_message('create'), "data": response.data}, status=status.HTTP_201_CREATED)
