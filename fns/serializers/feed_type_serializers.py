from common.mixins import BaseEnterpriseAuditSerializer
from fns.models import FeedType


class FeedTypeSerializer(BaseEnterpriseAuditSerializer):
    class Meta:
        model = FeedType
        fields = [
            "name",
            "brand",
            "feed_source",
            "composition",
            "unit_price",
            "created_by",
            "updated_by",
            "created_on",
            "updated_on",
        ]
