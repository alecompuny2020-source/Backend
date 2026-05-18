from common.mixins import BaseEnterpriseAuditSerializer
from sfap.models import Incubator, IncubationCycle


class IncubatorSerializer(BaseEnterpriseAuditSerializer):
    class Meta:
        model = Incubator
        fields = [
            'name', 'features', 'capacity', 'last_sanitized', 'is_active',
            'current_occupancy', 'available_space', 'availability_date',
            'created_by', 'updated_by', 'created_on', 'updated_on'
        ]
        read_only_fields = ['id', 'current_occupancy', 'available_space', 'availability_date']


class IncubationCycleSeializer(BaseEnterpriseAuditSerializer):
    class Meta:
        model = IncubationCycle
        fields = [
            'cycle_number', 'breeder_flock', 'hatcher', 'eggs_set_count',
            'expected_hatch_date', 'incubation_logs', 'actual_hatch_date',
            'status', 'total_loss', 'created_by', 'updated_by', 'created_on',
            'updated_on'
        ]
