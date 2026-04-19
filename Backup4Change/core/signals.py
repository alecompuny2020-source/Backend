from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm
from hrms.models import Department
from sfap.models import Farm
from helpers.permissions_config import PERM_CONFIG

@receiver(post_save, sender=Department)
@receiver(post_save, sender=Farm)
def auto_assign_permissions(sender, instance, created, **kwargs):
    if created:
        model_name = sender.__name__ # "Department" or "Farm"
        app_label = sender._meta.app_label # "hrms" or "sfap"
        config = PERM_CONFIG.get(model_name, {})

        for group_name, perms in config.items():
            # 1. Get or create the group
            group, _ = Group.objects.get_or_create(name=group_name)

            for perm_code in perms:
                # 2. Construct the FULL permission string
                # This results in "hrms.view_department"
                full_perm = f"{app_label}.{perm_code}"

                # 3. Assign to the instance
                assign_perm(full_perm, group, instance)
