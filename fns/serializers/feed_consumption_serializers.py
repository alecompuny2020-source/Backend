from common.mixins import BaseEnterpriseAuditSerializer
from fns.models import FeedConsumption


class FeedConsumptionSerializer(BaseEnterpriseAuditSerializer):
    class Meta:
        model = FeedConsumption
        fields = [
            "batch",
            "feed_type",
            "quantity_used_kg",
            "waste_amount_kg",
            "water_liters_added",
            "consumption_notes",
            "actual_intake",
            "created_by",
            "updated_by",
            "created_on",
            "updated_on",
        ]
