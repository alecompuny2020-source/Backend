from ipss.models import Product, ProductVariant
from common.mixins import BaseEnterpriseAuditSerializer
from rest_framework import serializers


class ProductSerializers(BaseEnterpriseAuditSerializer):
    class Meta:
        model = Product
        fields = [
            'id', 'name',
            'category',
            'specs',
            'created_by',
            'updated_by',
            'created_on',
            'updated_on'
        ]


class ProductVariantSerializers(BaseEnterpriseAuditSerializer):
    product = serializers.CharField(source = "product.name", read_only=True)
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'product',
            'cut_type',
            'storage_state',
            'fat_level',
            'sku',
            'price',
            'is_active',
            'variant_metadata',
            'created_by',
            'updated_by',
            'created_on',
            'updated_on'
        ]
