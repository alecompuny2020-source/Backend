from rest_framework_guardian.filters import ObjectPermissionsFilter
from rest_framework import filters
from rest_framework.permissions import IsAuthenticated, DjangoObjectPermissions

class EnterpriseObjectLevelPermissionMixin:
    """
    Mixin to inject row-level object security constraints
    only where explicitly inherited.
    """
    permission_classes = [IsAuthenticated, DjangoObjectPermissions]
    filter_backends = [ObjectPermissionsFilter, filters.SearchFilter, filters.OrderingFilter]

    def get_permissions(self):
        """
        Bypasses any public 'AllowAny' logic from the base class
        to guarantee strict object tracking across all methods.
        """
        return [permission() for permission in self.permission_classes]
