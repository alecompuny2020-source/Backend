from rest_framework import serializers

from common.mixins import BaseEnterpriseAuditSerializer
from sfap.models import CropProduction, EcologicalInput, FeedIngredientStock


class CropProductionSerializer(BaseEnterpriseAuditSerializer):

    class Meta:
        model = CropProduction
        fields = [
            "id",
            "block",
            # "crop_name",
            "planting_date",
            "harvest_date",
            "status",
            "manure_used_kg",
            "production_metadata",
            "estimated_yield_kg",
            "actual_yield_kg",
            "created_by",
            "updated_by",
            "created_on",
            "updated_on",
        ]


class EcologicalInputSerializer(BaseEnterpriseAuditSerializer):

    class Meta:
        model = EcologicalInput
        fields = [
            "id",
            "input_name",
            "quantity",
            "unit",
            "estimated_cost",
            "origin",
            "created_by",
            "updated_by",
            "created_on",
            "updated_on",
        ]


class LogCropHarvestSerializer(serializers.Serializer):
    actual_yield_kg = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0.01
    )
    unit_cost_tzs = serializers.DecimalField(
        max_digits=12, decimal_places=2, default=0.00, min_value=0.00
    )


class FeedIngredientStockSerializer(BaseEnterpriseAuditSerializer):
    last_updated = serializers.DateTimeField(
        source="updated_on", read_only=True, format="%Y-%m-%dT%H:%M:%S%z"
    )

    class Meta:
        model = FeedIngredientStock
        fields = [
            "id",
            "farm",
            "ingredient_name",
            "available_qty_kg",
            "unit_cost_per_kg",
            "created_by",
            "updated_by",
            "created_on",
            "last_updated",
        ]
