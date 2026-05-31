from rest_framework import serializers

from common.mixins import BaseEnterpriseAuditSerializer
from sfap.models import (
    Batch,
    BreederFlock,
    DailyObservation,
    Farm,
    FarmBlock,
    FarmShed,
    ManagerHistory,
)


class FarmSerializers(BaseEnterpriseAuditSerializer):
    class Meta:
        model = Farm
        fields = [
            "id",
            "name",
            "manager",
            "site_config",
            "is_quarantined",
            "region",
            "district",
            "ward",
            "postcode",
            "address_metadata",
            "full_address",
            "is_active",
            "created_by",
            "updated_by",
            "created_on",
            "updated_on",
        ]
        read_only_fields = ["id", "full_address"]


class FarmManagerHistorySerializer(serializers.ModelSerializer):
    farm = serializers.CharField(source="farm.get_farm_details()", read_only=True)

    class Meta:
        model = ManagerHistory
        fields = [
            "id",
            "farm",
            "plant",
            "manager",
            "start_date",
            "end_date",
            "tenure_metadata",
            "is_current",
        ]


class FarmShedSerializer(BaseEnterpriseAuditSerializer):
    class Meta:
        model = FarmShed
        fields = [
            "id",
            "name",
            "farm",
            "capacity",
            "shed_metadata",
            "last_empty_date",
            "is_active",
            "rest_days",
            "created_by",
            "updated_by",
            "created_on",
            "updated_on",
        ]


class FarmBlockSerializer(BaseEnterpriseAuditSerializer):
    class Meta:
        model = FarmBlock
        fields = [
            "id",
            "farm",
            "name",
            "size_acres",
            "status",
            "soil_data",
            "created_by",
            "updated_by",
            "created_on",
            "updated_on",
        ]


class FarmBatchSerializer(BaseEnterpriseAuditSerializer):
    class Meta:
        model = Batch
        fields = [
            "id",
            "batch_id",
            "shed",
            "bird_type",
            "initial_count",
            "current_count",
            "expected_depletion_date",
            "batch_details",
            "status",
            "age_in_days",
            "created_by",
            "updated_by",
            "created_on",
            "updated_on",
        ]
        read_only_fields = ["id", "age_in_days", "batch_id"]


class DailyObservationSerializer(BaseEnterpriseAuditSerializer):
    class Meta:
        model = DailyObservation
        fields = [
            "id",
            "batch",
            "mortality_count",
            "culls",
            "environmental_data",
            "created_by",
            "updated_by",
            "created_on",
            "updated_on",
        ]
        read_only_fields = ["id"]


class BreederFlockSerializer(BaseEnterpriseAuditSerializer):
    class Meta:
        model = BreederFlock
        fields = [
            "id",
            "source_batch",
            "breed_line",
            "genetic_source",
            "traits",
            "lifetime_hatchability",
            "created_by",
            "updated_by",
            "created_on",
            "updated_on",
        ]
        read_only_fields = ["id", "lifetime_hatchability"]
