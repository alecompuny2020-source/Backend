# serializers.py
class SaleItemSerializer(serializers.ModelSerializer):
    product_display_name = serializers.SerializerMethodField()

    class Meta:
        model = SaleItem
        fields = [
            "id",
            "product_display_name",
            "quantity",
            "unit_price",
            "line_total",
        ]

    def get_product_display_name(self, obj):
        # Kama ni mauzo ya pakiti, chukua jina lake na QR code
        if obj.packaged_product:
            return f"{obj.packaged_product.variant_ref.name} (PKT - {obj.packaged_product.label_code})"
        # Kama ni mauzo ya kukatwa (Loose/Bulk)
        return f"{obj.product_stock.product_type.name} (Bulk)"
