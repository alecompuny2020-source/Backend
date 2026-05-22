from sfap.models import CropProduction
from common.mixins import BaseEnterpriseAuditSerializer


class CropProductionSerializer(serializers.ModelSerializer):

    class Meta:
        model = CropProduction
        fields = [
            'id', 'block', 'crop_name', 'planting_date', 'harvest_date', 'manure_used_kg',
            'production_metadata', 'created_by', 'updated_by','created_on',
            'updated_on'
        ]
