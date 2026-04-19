from rest_framework import serializers
from django.utils import timezone
from .models import (
    Farm, ManagerHistory, FarmShed, Batch, DailyObservation, BreederFlock, Incubator,
    IncubationCycle, HatchRecord, HealthProtocol, MedicalRecord, DiseaseOutbreak,
    DiseaseOutbreak, FarmVehicle, TransportMovement
    )

from helpers.choices import now, now_iso


class FarmSerializer(serializers.ModelSerializer):
    farm_manager = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    is_quarantined = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    last_updated = serializers.SerializerMethodField()

    class Meta:
        model = Farm
        fields = [
            "name", "region", "gps_coordinates", "site_config", "farm_manager",
            "is_quarantined", "is_active", "created_by", "created_on", "updated_by",
            "last_updated"
        ]
        extra_kwargs = {
            "read_only_fields" : {
                "id", "created_by", "created_on", "farm_manager", "updated_by",
                "last_updated"
            }
        }
        write_only_fields = ["manager"]

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user
        farm = Farm.objects.create(**validated_data)
        return farm

    def update(self, instance, validated_data):
        request = self.context['request']
        validated_data['updated_by'] = request.user
        validated_data['updated_on'] = now_iso
        farm = Farm.objects.update(**validated_data)
        return farm

    def get_farm_manager(self, obj) -> str:
        return obj.manager.user.get_full_name() if obj.manager else None

    def get_created_by(self, obj) -> str:
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj) -> str:
        return obj.updated_by.get_full_name() if obj.updated_by else None

    def get_last_updated(self, obj) -> str:
        return obj.updated_on if obj.updated_on else None

    def get_is_active(self, obj) -> str:
        return f'YES' if obj.is_active else f'NO'

    def get_is_quarantined(self, obj) -> str:
        return f'YES' if obj.is_quarantined else f'NO'



class FarmShedSerializer(serializers.ModelSerializer):
    farm = serializers.SerializerMethodField()
    last_empty_date = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    last_updated = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = FarmShed
        fields = ['id', 'name', 'farm', 'capacity', 'shed_metadata', 'last_empty_date'
            ,'is_active', "created_by", "created_on", "updated_by", "last_updated"
        ]
        extra_kwargs = {
            "read_only_fields" : {
                "id", "last_empty_date", "last_cleared", "created_by", "created_on",
                "updated_by"
            }
        }
        write_only_fields = ["farm"]

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user
        shed = FarmShed.objects.create(**validated_data)
        return shed

    def update(self, instance, validated_data):
        request = self.context['request']
        ivalidated_data['updated_by'] = request.user
        validated_data['updated_on'] = now_iso
        return FarmShed.objects.update(**validated_data)

    def get_farm(self, obj) -> str:
        return obj.farm.get_farm_details() if obj.farm else 'Unassigned'

    def get_last_empty_date(self, obj) -> str:
        return obj.last_empty_date if obj.last_empty_date else 'Not specified'

    def get_is_active(self, obj) -> str:
        return f'YES' if obj.is_active else f'NO'

    def get_created_by(self, obj) -> str:
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj) -> str:
        return obj.updated_by.get_full_name() if obj.updated_by else None

    def get_last_updated(self, obj) -> str:
        return obj.updated_on if obj.updated_on else None


class BatchSerializer(serializers.ModelSerializer):
    expected_depletion_date = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    shed = serializers.SerializerMethodField()

    class Meta:
        model = Batch
        fields = [
            'batch_id', 'shed', 'bird_type', 'initial_count', 'current_count',
            'expected_depletion_date', 'batch_details', 'status', 'created_by',
            'created_on', 'updated_by', 'updated_on', 'id'
        ]
        extra_kwargs = {
            "read_only_fields" : {
                "created_by", "created_on", "updated_by"
            }
        }

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user
        batch = Batch.objects.create(**validated_data)
        return batch

    def update(self, instance, validated_data):
        request = self.context['request']
        validated_data['updated_by'] = request.user
        validated_data['updated_on'] = now_iso
        return Batch.objects.update(**validated_data)

    def get_expected_depletion_date(self, obj) -> str:
        return obj.expected_depletion_date if obj.expected_depletion_date else 'Not specified'

    def get_created_by(self, obj) -> str:
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj) -> str:
        return obj.updated_by.get_full_name() if obj.updated_by else None

    def get_shed(self, obj) -> str:
        return obj.shed.name if obj.shed else 'Unassigned'


class DailyObservationSerializer(serializers.ModelSerializer):
    batch = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = DailyObservation
        fields = [
            'batch', 'mortality_count', 'culls', 'environmental_data', 'created_by',
            'created_on', 'updated_by', 'updated_on', 'id'
        ]

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user
        record = DailyObservation.objects.create(**validated_data)
        return record

    def update(self, instance, validated_data):
        request = self.context['request']
        validated_data['updated_by'] = request.user
        validated_data['updated_on'] = now_iso
        return DailyObservation.objects.update(**validated_data)

    def get_batch(self, obj) -> str:
        return f'{obj.batch.shed.name}-{obj.batch.batch_id}' if obj.batch else 'Not specified'

    def get_created_by(self, obj) -> str:
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj) -> str:
        return obj.updated_by.get_full_name() if obj.updated_by else None



class BreederFlockSerializer(serializers.ModelSerializer):
    source_batch = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = BreederFlock
        fields = [
            'id','source_batch', 'breed_line', 'genetic_source', 'traits', 'created_by',
            'created_on', 'updated_by', 'updated_on'
        ]
        extra_kwargs = {
            "read_only_fields" : {
                "created_by", "created_on", "updated_by", 'id'
            }
        }

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user
        record = BreederFlock.objects.create(**validated_data)
        return record

    def update(self, instance, validated_data):
        request = self.context['request']
        validated_data['updated_by'] = request.user
        validated_data['updated_on'] = now_iso
        return BreederFlock.objects.update(**validated_data)

    def get_source_batch(self, obj) -> str:
        return f'{obj.source_batch.shed.name}-{obj.source_batch.batch_id}' if obj.source_batch else 'Not specified'

    def get_created_by(self, obj) -> str:
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj) -> str:
        return obj.updated_by.get_full_name() if obj.updated_by else None


class IncubatorSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    last_sanitized = serializers.SerializerMethodField()

    class Meta:
        model = Incubator
        fields = [
            'id', 'name', 'features', 'capacity', 'last_sanitized', 'is_active',
            'created_by', 'created_on', 'updated_by', 'updated_on'
        ]
        extra_kwargs = {
            "read_only_fields" : {
                "created_by", "created_on", "updated_by", 'id'
            }
        }

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user
        record = Incubator.objects.create(**validated_data)
        return record

    def update(self, instance, validated_data):
        request = self.context['request']
        validated_data['updated_by'] = request.user
        validated_data['updated_on'] = now_iso
        return Incubator.objects.update(**validated_data)

    def get_created_by(self, obj) -> str:
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj) -> str:
        return obj.updated_by.get_full_name() if obj.updated_by else None

    def get_is_active(self, obj) -> str:
        return 'YES' if obj.is_active else 'NO'

    def get_last_sanitized(self, obj) -> str:
        return obj.last_sanitized if obj.last_sanitized else 'Not yet sanitized'


class IncubationCycleserializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    expected_hatch_date = serializers.SerializerMethodField()
    actual_hatch_date = serializers.SerializerMethodField()

    class Meta:
        model = IncubationCycle
        fields = [
            'id', 'cycle_id', 'breeder_flock', 'hatcher', 'eggs_set_count',
            'expected_hatch_date', 'incubation_logs', 'actual_hatch_date', 'status',
            'created_by', 'created_on', 'updated_by', 'updated_on'
        ]
        extra_kwargs = {
            "read_only_fields" : {
                "created_by", "created_on", "updated_by", 'id'
            }
        }

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user
        record = IncubationCycle.objects.create(**validated_data)
        return record

    def update(self, instance, validated_data):
        request = self.context['request']
        validated_data['updated_by'] = request.user
        validated_data['updated_on'] = now_iso
        return IncubationCycle.objects.update(**validated_data)

    def get_created_by(self, obj) -> str:
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj) -> str:
        return obj.updated_by.get_full_name() if obj.updated_by else None

    def get_expected_hatch_date(self, obj) -> str:
        return obj.expected_hatch_date if obj.expected_hatch_date else 'Not specified'

    def get_expected_hatch_date(self, obj) -> str:
        return obj.actual_hatch_date if obj.actual_hatch_date else 'Not specified'


class HatchRecordSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    is_added_to_inventory = serializers.SerializerMethodField()

    class Meta:
        model = HatchRecord
        fields = [
            'id', 'incubation_cycle', 'is_added_to_inventory', 'destination_batch',
            'total_chicks_hatched', 'grade_a_chicks', 'grade_b_chicks',
            'grade_c_chicks', 'quality_metrics', 'hatchability_percentage',
            'cull_weight_total', 'created_by', 'created_on', 'updated_by', 'updated_on'
        ]
        extra_kwargs = {
            "read_only_fields" : {
                "created_by", "created_on", "updated_by", 'id'
            }
        }

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user
        record = HatchRecord.objects.create(**validated_data)
        return record

    def update(self, instance, validated_data):
        request = self.context['request']
        validated_data['updated_by'] = request.user
        validated_data['updated_on'] = now_iso
        return HatchRecord.objects.update(**validated_data)

    def get_created_by(self, obj) -> str:
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj) -> str:
        return obj.updated_by.get_full_name() if obj.updated_by else None

    def get_is_added_to_inventory(self, obj) -> str:
        return 'YES' if obj.is_added_to_inventory else 'NO'



class HealthProtocolSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = HealthProtocol
        fields = [
            'id', 'name', 'target_bird_type', 'protocol_steps','description',
            'created_by', 'created_on', 'updated_by', 'updated_on'
        ]
        extra_kwargs = {
            "read_only_fields" : {
                "created_by", "created_on", "updated_by", 'id'
            }
        }

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user
        record = HealthProtocol.objects.create(**validated_data)
        return record

    def update(self, instance, validated_data):
        request = self.context['request']
        validated_data['updated_by'] = request.user
        validated_data['updated_on'] = now_iso
        return HealthProtocol.objects.update(**validated_data)

    def get_created_by(self, obj) -> str:
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj) -> str:
        return obj.updated_by.get_full_name() if obj.updated_by else None


class MedicalRecordSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    batch = serializers.SerializerMethodField()
    withdrawal_end_date = serializers.SerializerMethodField()

    class Meta:
        model = MedicalRecord
        fields = [
            'id', 'batch', 'date_of_administration', 'record_type', 'event_details', 'cost', 'notes',
            'withdrawal_end_date', 'created_by', 'created_on', 'updated_by',
            'updated_on'
        ]
        extra_kwargs = {
            "read_only_fields" : {
                "created_by", "created_on", "updated_by", 'id'
            }
        }

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user
        record = MedicalRecord.objects.create(**validated_data)
        return record

    def update(self, instance, validated_data):
        request = self.context['request']
        validated_data['updated_by'] = request.user
        validated_data['updated_on'] = now_iso
        return MedicalRecord.objects.update(**validated_data)

    def get_created_by(self, obj) -> str:
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj) -> str:
        return obj.updated_by.get_full_name() if obj.updated_by else None

    def get_batch(self, obj) -> str:
        return f'{obj.batch.shed.name}-{obj.batch.batch_id}' if obj.batch else 'Not specified'

    def get_withdrawal_end_date(self, obj) -> str:
        return obj.withdrawal_end_date if obj.withdrawal_end_date else 'Not specified'


class DiseaseOutbreakSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    batch = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()

    class Meta:
        model = DiseaseOutbreak
        fields = [
            'id', 'batch', 'suspected_disease', 'end_date','diagnostic_data',
            'status', 'created_by', 'created_on', 'updated_by', 'updated_on'
        ]
        extra_kwargs = {
            "read_only_fields" : {
                "created_by", "created_on", "updated_by", 'id'
            }
        }

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user
        record = DiseaseOutbreak.objects.create(**validated_data)
        return record

    def update(self, instance, validated_data):
        request = self.context['request']
        validated_data['updated_by'] = request.user
        validated_data['updated_on'] = now_iso
        return DiseaseOutbreak.objects.update(**validated_data)

    def get_created_by(self, obj) -> str:
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj) -> str:
        return obj.updated_by.get_full_name() if obj.updated_by else None

    def get_batch(self, obj) -> str:
        return f'{obj.batch.shed.name}-{obj.batch.batch_id}' if obj.batch else 'Not specified'

    def end_date(self, obj) -> str:
        return obj.end_date if obj.end_date else 'Not specified'


class FarmVehicleSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = FarmVehicle
        fields = [
            "id", "plate_number", "vehicle_type", "max_payload_kg", "vehicle_specs"
            ,"is_active", "created_by", "created_on", "updated_by", "updated_on"
        ]
        extra_kwargs = {
            "read_only_fields" : {
                "id", "created_by", "created_on", "updated_by", "updated_on"
            }
        }

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user
        record = FarmVehicle.objects.create(**validated_data)
        return record

    def update(self, instance, validated_data):
        request = self.context['request']
        validated_data['updated_by'] = request.user
        validated_data['updated_on'] = now_iso
        return FarmVehicle.objects.update(**validated_data)

    def get_created_by(self, obj) -> str:
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj) -> str:
        return obj.updated_by.get_full_name() if obj.updated_by else None

    def get_is_active(self, obj) -> str:
        return f'YES' if obj.is_active else f'NO'


class TransportMovementSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    vehicle = serializers.SerializerMethodField()
    driver = serializers.SerializerMethodField()

    class Meta:
        model = TransportMovement
        fields = [
            'id', 'vehicle', 'driver', 'origin', 'destination', 'departure_time',
            'arrival_time', 'transit_data', 'created_by', 'created_on',
            'updated_by', 'updated_on'
        ]
        extra_kwargs = {
            "read_only_fields" : {
                "created_by", "created_on", "updated_by", "id", "updated_on"
            }
        }

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user
        record = TransportMovement.objects.create(**validated_data)
        return record

    def update(self, instance, validated_data):
        request = self.context['request']
        validated_data['updated_by'] = request.user
        validated_data['updated_on'] = now_iso
        return TransportMovement.objects.update(**validated_data)

    def get_created_by(self, obj) -> str:
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj) -> str:
        return obj.updated_by.get_full_name() if obj.updated_by else None

    def get_driver(self, obj) -> str:
        return obj.driver.user.get_full_name() if obj.driver else 'Driver'

    def get_vehicle(self, obj) -> str:
        return obj.vehicle.plate_number if obj.vehicle else 'Vehicle'



class FarmManagerHistorySerializer(serializers.ModelSerializer):
    manager = serializers.SerializerMethodField()
    farm = serializers.SerializerMethodField()
    plant = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = ManagerHistory
        fields = ["id", "farm", "plant", "manager", "start_date", "end_date", "tenure_metadata", "is_current"]
        extra_kwargs = {
            "read_only_fields" : {
                'id'
            }
        }

    def get_manager(self, obj) -> str:
        return obj.manager.user.get_full_name() if obj.manager else None

    def get_farm(self, obj) -> str:
        return obj.farm.get_farm_details() if obj.farm else 'Unassigned'

    def get_plant(self, obj) -> str:
        return obj.plant.get_plant_details() if obj.plant else 'Unassigned'

    def get_end_date(self, obj) -> str:
        return obj.end_date if obj.end_date else 'Not specified'

    def get_is_current(self, obj) -> str:
        return f'YES' if obj.is_current else f'NO'
