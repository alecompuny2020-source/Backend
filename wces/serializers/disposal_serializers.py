from common.mixins import BaseEnterpriseAuditSerializer
from wces.models import DisposalArea, WasteOutflow


class DisposalAreaSerializers(BaseEnterpriseAuditSerializer):
    class Meta:
        model = DisposalArea
        fields = [
            'name', 'disposal_metadata', 'is_active', 'created_by',
            'updated_by', 'created_on', 'updated_on'
        ]


class WasteOutflowSerializers(BaseEnterpriseAuditSerializer):
    class Meta:
        model = WasteOutflow
        fields = [
            'collection_logs', 'destination', 'total_weight', 'exit_metadata',
            'net_financial_impact','created_by', 'updated_by', 'created_on',
            'updated_on'
        ]
