from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from sfap.models import Farm

class Command(BaseCommand):
    help = "Seed groups and permissions for Poultry Farm Management System"

    def handle(self, *args, **kwargs):
        farm_ct = ContentType.objects.get_for_model(Farm)

        roles = {
            "FLOCK_SHED_ATTENDANT": [
                "add_daily_observation",
                "log_mortality",
                "update_water_intake",
                "log_egg_collection",
            ],
            "FARM_MANAGER": [
                "approve_batch_movement",
                "view_kpi_dashboard",
                "assign_shed_worker",
                "manage_biosecurity_lockdown",
            ],
            "HATCHERY_SPECIALIST": [
                "manage_incubation_cycle",
                "log_hatch_results",
                "update_breeder_traits",
                "check_egg_fertility",
            ],
            "VETERINARY_OFFICER": [
                "prescribe_medication",
                "log_vaccination",
                "declare_disease_outbreak",
                "issue_health_clearance",
            ],
        }

        for role, actions in roles.items():
            group, _ = Group.objects.get_or_create(name=role)
            for action in actions:
                perm = Permission.objects.get(
                    codename=action,
                    content_type=farm_ct,
                )
                group.permissions.add(perm)

        self.stdout.write(self.style.SUCCESS("Roles and permissions seeded successfully"))


# {
#   "detail": "You do not have permission to perform this action."
# }
