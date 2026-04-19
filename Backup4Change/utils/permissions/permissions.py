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
