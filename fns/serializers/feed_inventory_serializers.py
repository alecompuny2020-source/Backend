from common.mixins import BaseEnterpriseAuditSerializer
from fns.models import FeedInventory


class FeedInventorySerializer(BaseEnterpriseAuditSerializer):
    class Meta:
        model = FeedInventory
        fields = [
            'feed_type', 'total_quantity_kg', 'reorder_level', 'stock_logs',
            'created_by', 'updated_by', 'created_on', 'updated_on'
        ]
