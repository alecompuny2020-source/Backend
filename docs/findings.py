
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action

class UserProfileViewSet(viewsets.GenericViewSet):
    """
    Unified ViewSet for granular user profile management.
    Uses a centralized dispatcher to handle CRUD operations across different entities.
    """
    permission_classes = [permissions.IsAuthenticated]

    # --- THE DRY ENGINE ---

    def _handle_action(self, instance_or_queryset, serializer_class, request,
                       many=False, success_msg="Operation successful"):
        """
        Generic action dispatcher to handle GET, POST, PUT, PATCH, DELETE
        for granular profile sections.
        """
        method = request.method.lower()

        # 1. RETRIEVE (GET)
        if method == "get":
            serializer = serializer_class(instance_or_queryset, many=many)
            return Response(serializer.data)

        # 2. CREATE (POST)
        if method == "post":
            # If it's a 1-to-1 relationship and exists, block POST
            if instance_or_queryset and not many:
                return Response({"error": "Resource already exists."}, status=status.HTTP_400_BAD_REQUEST)

            serializer = serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response({"detail": success_msg}, status=status.HTTP_201_CREATED)

        # 3. UPDATE (PUT/PATCH)
        if method in ["put", "patch"]:
            # For collections (Addresses), find specific item from request data
            obj = instance_or_queryset
            if many:
                obj_id = request.data.get("id")
                obj = instance_or_queryset.filter(id=obj_id).first()
                if not obj:
                    return Response({"error": "Item not found."}, status=status.HTTP_404_NOT_FOUND)

            if not obj:
                 return Response({"error": "Resource not found."}, status=status.HTTP_404_NOT_FOUND)

            serializer = serializer_class(obj, data=request.data, partial=(method == "patch"))
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"detail": success_msg})

        # 4. DELETE
        if method == "delete":
            obj = instance_or_queryset
            if many:
                obj_id = request.data.get("id")
                obj = instance_or_queryset.filter(id=obj_id).first()

            if not obj:
                return Response({"error": "Nothing to delete."}, status=status.HTTP_404_NOT_FOUND)

            # Special case for Profile Picture file cleanup
            if hasattr(obj, 'profile_picture') and hasattr(obj.profile_picture, 'delete'):
                obj.profile_picture.delete(save=False)
                obj.profile_picture = None
                obj.save()
            else:
                obj.delete()

            return Response({"detail": "Deleted successfully."})

    # --- DEDICATED ACTIONS ---

    @action(detail=False, methods=["get", "post", "put", "patch", "delete"])
    def personal_info(self, request):
        """Manage core personal details."""
        return self._handle_action(request.user, UserPersonalInfoSerializer, request)

    @action(detail=False, methods=["get", "put", "patch"])
    def contact_info(self, request):
        """Manage email and phone."""
        return self._handle_action(request.user, UserContactInfoSerializer, request)

    @action(detail=False, methods=["get", "post", "put", "patch", "delete"])
    def profile_picture(self, request):
        """Manage profile picture file."""
        return self._handle_action(request.user, ProfilePictureSerializer, request)

    @action(detail=False, methods=["get", "post", "put", "patch", "delete"])
    def addresses(self, request):
        """Manage user addresses (Collection)."""
        return self._handle_action(request.user.addresses.all(), UserAddressSerializer, request, many=True)

    @action(detail=False, methods=["get", "post", "put", "patch", "delete"])
    def preferences(self, request):
        """Manage user system preferences."""
        pref = getattr(request.user, 'preferences', None)
        return self._handle_action(pref, UserPreferenceSerializer, request)

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
