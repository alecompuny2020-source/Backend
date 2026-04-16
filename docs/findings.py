
class BaseEnterpriseSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        validated_data['updated_on'] = now_iso # Note: Ensure your model supports updated_on
        return super().update(instance, validated_data)


# MORE GRANULAR

from rest_framework import serializers
from helpers.choices import now_iso

class AuditFieldsMixin(serializers.ModelSerializer):
    """
    Enterprise mixin to handle ownership and YES/NO formatting.
    """
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


from rest_framework import serializers
from .models import * # Import your models
from core.mixins import AuditFieldsMixin

class FarmSerializer(AuditFieldsMixin):
    farm_manager = serializers.CharField(source='manager.user.get_full_name', read_only=True)

    class Meta:
        model = Farm
        fields = [
            "id", "name", "region", "gps_coordinates", "site_config", "farm_manager",
            "is_quarantined", "is_active", "created_by_name", "created_on",
            "updated_by_name", "updated_on"
        ]
        read_only_fields = ["id", "created_on", "updated_on"]

class FarmShedSerializer(AuditFieldsMixin):
    farm_details = serializers.CharField(source='farm.get_farm_details', read_only=True)

    class Meta:
        model = FarmShed
        fields = "__all__" # Use __all__ or specific list to keep it tight



from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from .models import *
from .serializers import *
from core.renderers import GenericPaginator # Using the new core folder

class BaseEnterpriseViewSet(viewsets.ModelViewSet):
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

# Now your ViewSets are incredibly clean:
class FarmViewSet(BaseEnterpriseViewSet):
    queryset = Farm.objects.all().select_related('manager__user')
    serializer_class = FarmSerializer
    filterset_fields = ["region", "is_active", "is_quarantined", "manager"]
    search_fields = ["name", "region"]

class FarmShedViewSet(BaseEnterpriseViewSet):
    queryset = FarmShed.objects.all().select_related('farm')
    serializer_class = FarmShedSerializer
    filterset_fields = ["name", "is_active"]


# Define common sets once
MANAGEMENT_BASE = ['view_employee', 'change_employee', 'can_change_employee_department']
FARM_ADMIN_BASE = MANAGEMENT_BASE + ['can_assign_shed', 'can_change_shed']

PERM_CONFIG = {
    'Employee': {
        'General Farm Manager': FARM_ADMIN_BASE + ['can_assign_plant'],
        'Farm Manager': FARM_ADMIN_BASE,
        'Lead Veterinary Officer': MANAGEMENT_BASE,
    }
}

class EnterpriseObjectPermission(permissions.DjangoObjectPermissions):
    """
    Standardizes object-level checks across the whole system.
    """
    authenticated_users_only = True

    # Override this to allow GET requests for everyone (if needed)
    # or keep it strict for Enterprise security.
    def has_permission(self, request, view):
        # Allow any authenticated user to hit the list view,
        # but filter the results using ObjectPermissionsFilter in the ViewSet.
        return request.user and request.user.is_authenticated

class CustomFarmPermissions(EnterpriseObjectPermission):
    """
    Specific to Farm logic. We define the map as a class attribute
    to keep it clean and performant.
    """
    # We explicitly define the full map to include your business actions
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': [
            '%(app_label)s.add_%(model_name)s',
            'farm.add_daily_observation',
            'farm.log_mortality'
        ],
        'PUT': [
            '%(app_label)s.change_%(model_name)s',
            'farm.approve_batch_movement'
        ],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }
