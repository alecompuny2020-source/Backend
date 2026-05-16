from django.contrib.auth.models import PermissionsMixin
import json

from django.conf import settings
from django.db import models, connections
# from django.contrib.gis.db import models as coordinates
import uuid
from rest_framework.response import Response
from django.forms.models import model_to_dict
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, viewsets, filters, status, permissions
from common.pagination import GenericEnteprisePaginator
from common.choices import current_time, now_iso, now


class BaseEnterpriseModelMixin(models.Model):
    """Reusable Base Model for Enterprise Apps"""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    class Meta:
        abstract = True


class BaseEnterpriseAuditModelMixin(BaseEnterpriseModelMixin):
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
        _("Updated On"), auto_now=False, db_index=True, null=True
    )

    class Meta(BaseEnterpriseModelMixin.Meta):
        abstract = True



class BaseEnterpriseViewSet(viewsets.ModelViewSet):
    """
    A base ViewSet to handle shared configuration and consistent success messages.
    """
    pagination_class = GenericEnteprisePaginator
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering = ['-id']

    def get_permissions(self):
        """
        Default baseline permissions for standard enterprise views.
        Public can read, authenticated users can write.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes]

    # Dynamically resolve model names for precise messages (e.g., "Department" instead of "Record")
    def get_model_name(self):
        return self.queryset.model._meta.verbose_name.title()

    def get_success_message(self):
        model_name = self.get_model_name()

        messages = {
            'create': f"{model_name} created successfully",
            'update': f"{model_name} was updated successfully",
            'partial_update': f"{model_name} was updated successfully",
            'destroy': f"{model_name} was deleted successfully"
        }
        # self.action automatically resolves to 'create', 'update', 'partial_update', or 'destroy'
        return messages.get(self.action, "Action successful")

    def perform_create(self, serializer):
        if hasattr(serializer.Meta.model, 'created_by'):
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()

    def perform_update(self, serializer):
        model = serializer.Meta.model
        save_kwargs = {}

        if hasattr(model, 'updated_by') and self.request.user.is_authenticated:
            save_kwargs['updated_by'] = self.request.user

        if hasattr(model, 'updated_on'):
            save_kwargs['updated_on'] = current_time

        # Single clean save execution for both audited and non-audited models
        serializer.save(**save_kwargs)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response(
            {"message": self.get_success_message()},
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(
            {"message": self.get_success_message()},
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response(
            {"message": self.get_success_message()},
            status=status.HTTP_200_OK
        )



class BaseEnterpriseAuditSerializer(serializers.ModelSerializer):
    """
    A dynamic base serializer that automatically exposes audit fields if they
    exist on the model, using 'created_by' and 'updated_by' for user full names.
    """
    created_by = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by = serializers.CharField(source='updated_by.get_full_name', read_only=True)

    created_on = serializers.DateTimeField(read_only=True, format="%Y-%m-%dT%H:%M:%S%z")
    updated_on = serializers.DateTimeField(read_only=True, format="%Y-%m-%dT%H:%M:%S%z")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Check if the model actually has the audit fields
        model = self.Meta.model
        audit_fields = ['created_by', 'updated_by', 'created_on', 'updated_on']

        for field_name in audit_fields:
            if not hasattr(model, field_name):
                # Dynamically pop the field out if the model doesn't support it
                self.fields.pop(field_name, None)

    def to_representation(self, instance):
        """ remove empty audit data from being returned """
        data = super().to_representation(instance)

        if data.get('updated_on') is None:
            data.pop('updated_on', None)

        if data.get('updated_by') is None:
            data.pop('updated_by', None)

        return data



class BaseAddressModelMixin(models.Model):
    """Reusable Base Address Model throughout the Enterprise"""
    region = models.CharField(max_length=100, db_index=True)
    district = models.CharField(max_length=100, db_index=True)
    ward = models.CharField(max_length=100)
    postcode = models.CharField(max_length=5, db_index=True)
    # gps_coordinates = coordinates.PointField(_("GPS Coordinates"), geography = True, null = True, blank = True, srid = 4326)

    # DYNAMIC FIELD (For Granularity)
    # Stores: street_name, plot_no, block_no, house_no, village, hamlet, landmark, etc.
    address_metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        abstract = True


#
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
