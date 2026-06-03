from ipss.models import ProductStock, StockMovement
from common.mixins import BaseEnterpriseAuditSerializer
from rest_framework import serializers


class ProductStockSerializers(BaseEnterpriseAuditSerializer):
    class Meta:
        model = ProductStock
        fields = [
            'id',
            'product_type',
            'storage_unit',
            'quantity_on_hand',
            'minimum_stock_level',
            'storage_temperature',
            'unit_of_measure',
            'readiness_status',
            'batch_number',
            'stock_metadata',
            'last_inspected',
            'days_to_expiry',
            'is_low_stock',
            'total_packaged_units_count',
            'total_packaged_weight',
            'created_by',
            'updated_by',
            'created_on',
            'updated_on'
        ]


class StockMovementSerializers(BaseEnterpriseAuditSerializer):
    class Meta:
        model = StockMovement
        fields = [
            'id', 'stock',
            'movement_type',
            'quantity_change',
            'units_change',
            'reference_id',
            'is_reversible',
            'movement_metadata',
            'created_by',
            'updated_by',
            'created_on',
            'updated_on'
        ]
