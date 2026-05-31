from common.mixins import BaseEnterpriseAuditSerializer
from ppms.models import ProcessingPlant, ProcessingSession


class ProcessingPlantSerializers(BaseEnterpriseAuditSerializer):
    class Meta:
        models = ProcessingPlant
        fields = [
            'name', 'location', 'plant_manager', 'plant_config', 'certification_info',
            'is_active', 'created_by', 'updated_by', 'created_on', 'updated_on'
        ]
