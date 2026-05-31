from common.mixins import BaseEnterpriseAuditSerializer
from sfap.models import HatchRecord, IncubationCycle, Incubator


class IncubatorSerializer(BaseEnterpriseAuditSerializer):
    class Meta:
        model = Incubator
        fields = [
            "id",
            "name",
            "features",
            "capacity",
            "last_sanitized",
            "is_active",
            "current_occupancy",
            "available_space",
            "availability_date",
            "created_by",
            "updated_by",
            "created_on",
            "updated_on",
        ]
        read_only_fields = [
            "id",
            "current_occupancy",
            "available_space",
            "availability_date",
        ]


class IncubationCycleSeializer(BaseEnterpriseAuditSerializer):
    class Meta:
        model = IncubationCycle
        fields = [
            "id",
            "cycle_number",
            "breeder_flock",
            "hatcher",
            "eggs_set_count",
            "expected_hatch_date",
            "incubation_logs",
            "actual_hatch_date",
            "status",
            "total_loss",
            "created_by",
            "updated_by",
            "created_on",
            "updated_on",
        ]
        read_only_fields = ["id"]


class HatchRecordSerializer(BaseEnterpriseAuditSerializer):
    class Meta:
        model = HatchRecord
        fields = [
            "id",
            "incubation_cycle",
            "is_added_to_inventory",
            "destination_batch",
            "total_chicks_hatched",
            "grade_a_chicks",
            "grade_b_chicks",
            "grade_c_chicks",
            "quality_metrics",
            "hatchability_percentage",
            "cull_weight_total",
            "created_by",
            "updated_by",
            "created_on",
            "updated_on",
        ]
        read_only_fields = ["id"]
