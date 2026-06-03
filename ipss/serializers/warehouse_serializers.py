from rest_framework import serializers

from common.mixins import BaseEnterpriseAuditSerializer
from ipss.models import StorageUnit, WarehouseLocation, Zone


class WarehouseLocationSerializers(BaseEnterpriseAuditSerializer):
    class Meta:
        model = WarehouseLocation
        fields = [
            "id",
            "name",
            "code",
            "is_active",
            "created_by",
            "updated_by",
            "created_on",
            "updated_on",
        ]


class ZoneSerializers(BaseEnterpriseAuditSerializer):
    warehouse = serializers.CharField(source="warehouse.name", read_only=True)

    class Meta:
        model = Zone
        fields = [
            "id",
            "warehouse",
            "name",
            "code",
            "created_by",
            "updated_by",
            "created_on",
            "updated_on",
        ]


class StorageUnitSerializers(BaseEnterpriseAuditSerializer):
    zone = serializers.CharField(source="zone.name", read_only=True)

    class Meta:
        model = StorageUnit
        fields = [
            "id",
            "zone",
            "unit_code",
            "unit_type",
            "max_capacity",
            "created_by",
            "updated_by",
            "created_on",
            "updated_on",
        ]
