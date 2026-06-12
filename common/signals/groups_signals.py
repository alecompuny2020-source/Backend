import logging

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from common.permissions.config import PERM_CONFIG

logger = logging.getLogger(__name__)


@receiver(post_migrate)
def sync_enterprise_infrastructure(sender, **kwargs):
    """
    Executed on system migration deployment. Guarantees all custom non-CRUD verbs
    and functional system corporate Groups exist seamlessly in the database schema.
    """
    app_config = sender

    if not any(model_name in app_config.models for model_name in PERM_CONFIG.keys()):
        return

    logger.info("Initializing Enterprise Security Matrix Provisioning...")
    print("Initializing Enterprise Security Matrix Provisioning...")

    try:
        with transaction.atomic():
            model_classes = []
            for model_name in PERM_CONFIG.keys():
                try:
                    model_classes.append(app_config.get_model(model_name))
                except LookupError:
                    continue

            if not model_classes:
                return

            content_types = ContentType.objects.get_for_models(*model_classes)

            for model_class in model_classes:
                model_name = model_class.__name__
                content_type = content_types.get(model_class)

                if not content_type:
                    logger.warning(
                        f"ContentType haikupatikana bado kwa ajili ya Model '{model_name}'."
                    )
                    print(
                        f"ContentType haikupatikana bado kwa ajili ya Model '{model_name}'."
                    )
                    continue

                roles = PERM_CONFIG.get(model_name, {})

                for role_name, permissions in roles.items():
                    group, _ = Group.objects.get_or_create(name=role_name)

                    permissions_to_add = []

                    for perm_codename in permissions:
                        is_standard = any(
                            perm_codename.startswith(v)
                            for v in ["add_", "change_", "delete_", "view_"]
                        )

                        if not is_standard:
                            human_name = perm_codename.replace("_", " ").capitalize()
                            Permission.objects.get_or_create(
                                codename=perm_codename,
                                content_type=content_type,
                                defaults={"name": human_name},
                            )

                        try:
                            perm_obj = Permission.objects.get(
                                codename=perm_codename, content_type=content_type
                            )
                            permissions_to_add.append(perm_obj)
                        except Permission.DoesNotExist:
                            logger.debug(
                                f"Permission '{perm_codename}' missing during setup."
                            )
                            print(f"Permission '{perm_codename}' missing during setup.")
                            continue

                    if permissions_to_add:
                        group.permissions.add(*permissions_to_add)

        try:
            from common.signals.permission_signals import EnterpriseGroupCache

            EnterpriseGroupCache.clear()
        except ImportError:
            pass

        logger.info("Enterprise Security Matrix successfully synced.")
        print("Enterprise Security Matrix successfully synced.")

    except Exception as e:
        logger.error(f"Hitilafu kubwa kwenye usanidi wa makundi ya usalama: {e}")
        print(f"Hitilafu kubwa kwenye usanidi wa makundi ya usalama: {e}")
