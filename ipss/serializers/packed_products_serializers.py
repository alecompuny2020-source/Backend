from rest_framework import serializers

from common.mixins import BaseEnterpriseAuditSerializer
from ipss.models import PackagedProduct


class PackagedProductSerializers(BaseEnterpriseAuditSerializer):
    class Meta:
        model = PackagedProduct
        fields = [
            "id",
            "session",
            "variant_ref",
            "production_line",
            "status",
            "label_code",
            "weight",
            "units_inside_package",
            "packaging_metadata",
            "expiry_date",
            "created_by",
            "updated_by",
            "created_on",
            "updated_on",
        ]
