from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Department
from .dep_dict import DEP_DICT

@receiver(post_migrate)
def provision_enterprise_departments(sender, **kwargs):
    """
    Automated seed module ensuring every operational department is structurally
    provisioned into your custom database tables during deployments.

    - Creates or matches departments safely by their Unique Code to prevent collisions
    """
    if sender.name != 'your_main_app_name':
        return

    for key, data in DEP_DICT.items():
        Department.objects.get_or_create(
            code=data["code"],
            defaults={
                "name": data["name"],
                "description": data["description"],
                "is_active": data["is_active"]
            }
        )
