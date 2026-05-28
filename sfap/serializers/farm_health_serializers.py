from sfap.models import HealthProtocol, MedicalRecord, DiseaseOutbreak
from common.mixins import BaseEnterpriseAuditSerializer


class HealthProtocolSerializer(BaseEnterpriseAuditSerializer):

    class Meta:
        model = HealthProtocol
        fields = [
            'id', 'name', 'target_bird_type', 'protocol_steps', 'description',
            'created_by', 'updated_by','created_on', 'updated_on'
        ]


class MedicalRecordSerializer(BaseEnterpriseAuditSerializer):

    class Meta:
        model = MedicalRecord
        fields = [
            'id', 'batch', 'date_of_administration', 'record_type', 'event_details',
            'cost', 'notes', 'withdrawal_end_date', 'is_in_withdrawal',
            'created_by', 'updated_by','created_on', 'updated_on'
        ]


class DiseaseOutbreakSerializer(BaseEnterpriseAuditSerializer):

    class Meta:
        model = DiseaseOutbreak
        fields = [
            'id', 'batch', 'suspected_disease', 'end_date', 'diagnostic_data',
            'status', 'created_by', 'updated_by','created_on', 'updated_on'
        ]
