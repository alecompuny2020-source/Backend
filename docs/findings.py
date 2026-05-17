
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


from rest_framework import viewsets, status, filters
from rest_framework.response import Response

class BaseEnterpriseViewSet(viewsets.ModelViewSet):
    """
    A base ViewSet to handle shared configuration and consistent success messages.
    """
    pagination_class = GenericEnteprisePaginator
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering = ['-id']

    # Dynamically resolve model names for precise messages (e.g., "Department" instead of "Record")
    def get_model_name(self):
        return self.queryset.model._meta.verbose_name.title()

    def get_success_message(self, action_name):
        model_name = self.get_model_name()

        messages = {
            'create': f"{model_name} created successfully",
            'update': f"{model_name} was updated successfully",
            'partial_update': f"{model_name} was updated successfully",
            'destroy': f"{model_name} was deleted successfully"
        }
        return messages.get(action_name, "Action successful")

    def finalize_response(self, request, response, *args, **kwargs):
        """
        Intercepts the standard DRF response to wrap standard mutations
        with your custom success message structure.
        """
        if response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK] and self.action in ['create', 'update', 'partial_update', 'destroy']:
            custom_data = {
                "message": self.get_success_message(self.action)
            }
            # Only include payload data if it's not a deletion request
            if self.action != 'destroy' and response.data is not None:
                custom_data["data"] = response.data

            response.data = custom_data
            response.content = None # Forces DRF to re-render the modified data dict

        return super().finalize_response(request, response, *args, **kwargs)


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



from django.db import models
from django.utils.translation import gettext_lazy as _

class EmployeeIDSequence(models.Model):
    """Tracks the auto-incrementing sequence counter for each distinct prefix code."""
    prefix = models.CharField(max_length=10, unique=True, help_text="e.g., HR, MFG, SLS")
    last_sequence = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "employee_id_sequence"
        verbose_name = _("Employee ID Sequence")
        verbose_name_plural = _("Employee ID Sequences")

    def __str__(self):
        return f"{self.prefix} - Last: {self.last_sequence}"


from django.db import transaction
from .models import EmployeeIDSequence

def generate_secure_employee_number(prefix_code: str, padding_length: int = 5) -> str:
    """
    Thread-safe, database-locked sequential ID generator.
    Example output: HR-00123, MFG-00456
    """
    # Clean and uppercase the prefix input
    prefix = prefix_code.strip().upper()

    # Force atomic transaction to handle concurrency safely
    with transaction.atomic():
        # select_for_update() locks the sequence row in the database until this transaction finishes
        sequence_tracker, created = EmployeeIDSequence.objects.select_for_update().get_or_create(
            prefix=prefix,
            defaults={'last_sequence': 0}
        )

        # Increment counter
        new_sequence = sequence_tracker.last_sequence + 1
        sequence_tracker.last_sequence = new_sequence
        sequence_tracker.save()

        # Format with zero padding (e.g., 1 -> '00001')
        padded_sequence = str(new_sequence).zfill(padding_length)

        return f"{prefix}-{padded_sequence}"


from django.db import models
from django.core.exceptions import ValidationError

class Employee(models.Model):
    # Relies on the Department model we designed earlier
    department = models.ForeignKey(
        'Department',
        on_delete=models.PROTECT,
        related_name='employees'
    )

    # Store the formatted secure ID string
    employee_number = models.CharField(
        max_length=25,
        unique=True,
        editable=False,
        db_index=True
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        # Only trigger generation if this is a brand-new database record insert
        if not self.pk or not self.employee_number:
            # Step A: Pick a code prefix from the linked department (e.g., 'Human Resources' -> 'HR')
            # You could add a explicit 'code' field on Department, or extract initials:
            if hasattr(self.department, 'code') and self.department.code:
                prefix = self.department.code
            else:
                # Fallback: Extract initials from department name (e.g. "Sales" -> "SLS")
                words = self.department.name.split()
                if len(words) >= 1 and len(words[0]) >= 3:
                    prefix = words[0][:3].upper() # Fallback first 3 letters
                else:
                    prefix = "EMP"

            # Step B: Securely compile and assign the string
            self.employee_number = generate_secure_employee_number(prefix_code=prefix, padding_length=5)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.employee_number}] {self.first_name} {self.last_name}"




























class BaseRole:
    """Base class to merge permissions from the class hierarchy."""
    permissions = {}

    @classmethod
    def get_all_permissions(cls):
        """Recursively collects and merges permissions from all parent roles."""
        combined_perms = {}
        # Traverse MRO in reverse to allow child classes to override/add to parents
        for base in reversed(cls.__mro__):
            if hasattr(base, 'permissions'):
                for model, perms in base.permissions.items():
                    if model not in combined_perms:
                        combined_perms[model] = set()
                    combined_perms[model].update(perms)

        # Convert sets back to lists for Django Guardian compatibility
        return {model: list(perms) for model, perms in combined_perms.items()}

# --- Functional Mixins (Groups of common permissions) ---

class BasicUserMixin:
    """Permissions common to almost every role."""
    permissions = {
        'User': ['view_user', 'change_user', 'can_change_self_password'],
        'UserAddress': ['add_user_address', 'change_user_address', 'delete_user_address', 'view_user_address'],
        'UserPreference': ['add_user_preference', 'change_user_preference', 'delete_user_preference', 'view_user_preference'],
        'UserActivityLog': ['view_activity_log'],
        'SearchHistory': ['add_user_search_history', 'delete_user_search_history', 'view_user_search_history'],
        'UserInterest': ['add_user_interests', 'change_user_interests', 'delete_user_interests', 'view_user_interests'],
        'Wishlist': ['add_user_wishlist', 'change_user_wishlist', 'delete_user_wishlist', 'view_user_wishlist'],
        'NextOfKin': ['add_next_of_kin', 'change_next_of_kin', 'delete_next_of_kin', 'view_next_of_kin'],
    }

class AdminMixin:
    """High-level system administration permissions."""
    permissions = {
        'User': [
            'add_user', 'delete_user', 'can_register_staff',
            'can_reset_password_other_user', 'can_deactivate_user', 'can_toggle_is_staff'
        ],
    }

# --- Concrete Roles ---

class StandardStaff(BaseRole, BasicUserMixin):
    """Most staff roles use exactly these base permissions."""
    pass

class Receptionist(StandardStaff):
    """Inherits everything from StandardStaff and adds specific User permissions."""
    permissions = {
        'User': ['add_user']
    }

class SystemAdministrator(StandardStaff, AdminMixin):
    """Combines basic user access with full administrative control."""
    pass

class ChiefExecutiveOfficer(SystemAdministrator):
    """Typically mirrors System Admin in your config."""
    pass

class GeneralFarmManager(StandardStaff):
    """Staff permissions plus specific farm management capabilities."""
    permissions = {
        'Employee': [
            'view_employee', 'change_employee', 'can_change_employee_department',
            'can_assign_shed', 'can_change_shed', 'can_assign_plant', 'can_change_plant'
        ]
    }

# --- Final Generation ---

# You can now generate your PERM_CONFIG dictionary automatically:
ROLES = {
    'Chief Executive Officer': ChiefExecutiveOfficer,
    'System Administrator': SystemAdministrator,
    'Receptionist': Receptionist,
    'General Farm Manager': GeneralFarmManager,
    # ... add other roles here
}

# Create the final dictionary for Django Guardian
RAW_CONFIG = {name: cls.get_all_permissions() for name, cls in ROLES.items()}

# Pivot the data so the signal can look it up by Model Name
PERM_CONFIG = {}
for role_name, model_map in RAW_CONFIG.items():
    for model_name, perms in model_map.items():
        if model_name not in PERM_CONFIG:
            PERM_CONFIG[model_name] = {}
        PERM_CONFIG[model_name][role_name] = perms


@receiver(post_save, sender=Department)
@receiver(post_save, sender=Farm)
def auto_assign_permissions(sender, instance, created, **kwargs):
    if not created:
        return

    model_name = sender.__name__
    app_label = sender._meta.app_label

    # Get the roles and perms specific to this model (e.g., 'Farm')
    # config will look like: {'General Farm Manager': ['view_farm', ...], 'Receptionist': [...]}
    model_config = PERM_CONFIG.get(model_name, {})

    for group_name, perms in model_config.items():
        group, _ = Group.objects.get_or_create(name=group_name)

        for perm_code in perms:
            full_perm = f"{app_label}.{perm_code}"
            assign_perm(full_perm, group, instance)
