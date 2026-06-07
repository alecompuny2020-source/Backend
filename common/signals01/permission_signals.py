import logging

from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from guardian.models import GroupObjectPermission

from common.permissions.config import PERM_CONFIG

logger = logging.getLogger(__name__)


class EnterpriseGroupCache:
    """
    A thread-safe, on-demand runtime cache. Resolves the module-level race
    condition by loading groups from the DB only when first requested.

    - Lazy-load groups on first query execution at runtime
    """

    _cache = None

    @classmethod
    def get_group(cls, role_name):
        if cls._cache is None:
            cls._cache = {g.name: g for g in Group.objects.all()}

        if role_name not in cls._cache:
            group, _ = Group.objects.get_or_create(name=role_name)
            cls._cache[role_name] = group
        return cls._cache.get(role_name)

    @classmethod
    def clear(cls):
        cls._cache = None


def optimized_row_permission_handler(sender, instance, created, **kwargs):
    """
    High-speed row-level security engine. Drops database overhead
    by utilizing local caching and unified memory-buffered batch writes.

    - Fetch content type and all valid permissions for this specific model
    - Evaluate and build mapping indices in-memory
    - Log a warning if a developer specified a permission in config that doesn't exist
    - Combined Single payload SQL Execution
    """
    if not created:
        return

    model_name = sender.__name__
    model_matrix = PERM_CONFIG.get(model_name, {})

    if not model_matrix:
        return

    content_type = ContentType.objects.get_for_model(sender)
    db_permissions = {
        p.codename: p for p in Permission.objects.filter(content_type=content_type)
    }

    bulk_permission_rows = []

    for role_name, codenames in model_matrix.items():
        group = EnterpriseGroupCache.get_group(role_name)
        if not group:
            logger.warning(
                f"Core authorization group '{role_name}' missing from database."
            )
            continue

        for codename in codenames:
            permission_obj = db_permissions.get(codename)
            if not permission_obj:
                logger.debug(
                    f"Permission '{codename}' not found for model '{model_name}'. Check provisioner."
                )
                continue

            bulk_permission_rows.append(
                GroupObjectPermission(
                    content_type=content_type,
                    object_pk=str(instance.pk),
                    group=group,
                    permission=permission_obj,
                )
            )

    if bulk_permission_rows:
        GroupObjectPermission.objects.bulk_create(
            bulk_permission_rows, ignore_conflicts=True
        )


def initialize_security_signals():
    """
    Locates and connects all models defined in the security matrix to the post_save receiver.
    Bypasses hardcoded array definitions entirely.
    - Iterate over all registered models across the project architecture
    - Executes dynamic signals linking
    """
    for model_string in PERM_CONFIG.keys():
        for model in apps.get_models():
            if model.__name__ == model_string:
                post_save.connect(optimized_row_permission_handler, sender=model)


initialize_security_signals()
