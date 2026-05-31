from common.mixins import BaseEnterpriseAuditSerializer
from ppms.models import ProcessingPlant, ProcessingSession


class ProcessingPlantSerializers(BaseEnterpriseAuditSerializer):
    class Meta:
        models = ProcessingPlant
        fields = [
            'name', 'location', 'plant_manager', 'plant_config', 'certification_info',
            'is_active', 'created_by', 'updated_by', 'created_on', 'updated_on'
        ]



class ProcessingSessionSerializers(BaseEnterpriseAuditSerializer):
    class Meta:
        model = ProcessingSession
        fields = [
            'plant',
        'source_batch',
        'assigned_workers',
        'birds_processed',
        'live_birds_count',
        'total_live_weight',
        'total_dressed_weight',
        'slaughter_data',
        'environmental_logs',
        'start_time',
        'end_time',
        'yield_percentage',
        'temperature_recorder',
        'rejected_birds',
        'bird_loss_count',
        'slaughter_shrinkage_kg',
'created_by',
'updated_by',
'created_on',
'updated_on'
        ]
