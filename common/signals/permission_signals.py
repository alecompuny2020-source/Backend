import logging

from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from guardian.models import GroupObjectPermission

from common.permissions.config import PERM_CONFIG

logger = logging.getLogger(__name__)


class EnterpriseGroupCache:
    """
    On-demand runtime cache inayosoma makundi yote kutoka kwenye DB mara moja tu.
    """

    _cache = None

    @classmethod
    def get_group(cls, role_name):
        if cls._cache is None:
            cls._cache = {g.name: g for g in Group.objects.all()}
        return cls._cache.get(role_name)

    @classmethod
    def clear(cls):
        cls._cache = None


def optimized_row_permission_handler(sender, instance, created, **kwargs):
    """
    Inashughulikia uwekaji wa Row-level permissions kwa kasi kubwa data mpya inapookolewa.
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
            continue  # Usalama: Kama group halipo bado kwenye DB, inaruka

        for codename in codenames:
            permission_obj = db_permissions.get(codename)
            if not permission_obj:
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
    """Inaunganisha models zote kwenye post_save dynamically."""
    for model_string in PERM_CONFIG.keys():
        for model in apps.get_models():
            if model.__name__ == model_string:
                post_save.connect(optimized_row_permission_handler, sender=model)
