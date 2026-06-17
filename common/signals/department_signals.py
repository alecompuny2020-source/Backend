from django.db.models.signals import post_migrate
from django.dispatch import receiver

from common.seeds.dep_dict import DEP_DICT


@receiver(post_migrate)
def provision_enterprise_departments(sender, **kwargs):
    """
    Automated seed module ensuring every operational department is structurally
    provisioned into your custom database tables during deployments.

    - Creates or matches departments safely by their Unique Code to prevent collisions
    """

    app_config = sender

    if app_config.label != "hrms":
        return

    Department = app_config.get_model("Department")
    created_count = 0
    existing_count = 0

    for key, data in DEP_DICT.items():
        obj, created = Department.objects.get_or_create(
            code=data["code"],
            defaults={
                "name": data["name"],
                "description": data["description"],
                "is_active": data["is_active"],
            },
        )

        if created:
            created_count += 1
        else:
            existing_count += 1

    print("\n" + "=" * 60)
    print(f" SUCCESS: HRMS Departments Provisioning Completed!")
    print(f" - Idara Mpya Zilizowekwa (Created): {created_count}")
    print(f" - Idara Zilizokuwepo Tayari (Skipped): {existing_count}")
    print("=" * 60 + "\n")
