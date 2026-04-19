from rest_framework import permissions

class GuardianObjectPermissions(permissions.DjangoObjectPermissions):
    """ Dynamically maps HTTP methods to Model permissions. """
    authenticated_users_only = True

    def get_required_object_permissions(self, method, model_cls):
        app_label = model_cls._meta.app_label
        model_name = model_cls._meta.model_name

        mapping = {
            'GET': [f'{app_label}.view_{model_name}'],
            'POST': [f'{app_label}.add_{model_name}'],
            'PUT': [f'{app_label}.change_{model_name}'],
            'PATCH': [f'{app_label}.change_{model_name}'],
            'DELETE': [f'{app_label}.delete_{model_name}'],
        }
        return mapping.get(method, [])

        
class GenericDepartmentPermissions(permissions.DjangoObjectPermissions):
    """ A custom permission for department """

    perms_map = {
        'GET': ["department.view_department"],
        'POST': [
            "department.add_department",
        ],
        'PUT': [
            "department.change_department",
        ],
        'PATCH': [
            "department.change_department",
        ],
        'DELETE': [
            "department.delete_department",
        ],
    }


class CustomFarmPermissions(permissions.DjangoObjectPermissions):
    perms_map = {
        'GET': ['farm.view_farm', 'farm.view_kpi_dashboard'],
        'POST': [
            'farm.add_daily_observation',
            'farm.log_mortality',
            'farm.update_water_intake',
            'farm.log_egg_collection',
            'farm.log_vaccination',
        ],
        'PUT': [
            'farm.change_farm',
            'farm.approve_batch_movement',
            'farm.manage_biosecurity_lockdown',
            'farm.prescribe_medication',
        ],
        'PATCH': [
            'farm.change_farm',
            'farm.update_breeder_traits',
        ],
        'DELETE': [
            'farm.delete_farm',
            'farm.declare_disease_outbreak',
            'farm.issue_health_clearance',
        ],
    }
