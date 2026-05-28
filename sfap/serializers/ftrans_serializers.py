from sfap.models import FarmVehicle, TransportMovement
from common.mixins import BaseEnterpriseAuditSerializer


class FarmVehicleSerializer(BaseEnterpriseAuditSerializer):

    class Meta:
        model = FarmVehicle
        fields = [
            'id', 'plate_number', 'vehicle_type', 'max_payload_kg', 'vehicle_specs',
            'is_active', 'created_by', 'updated_by','created_on', 'updated_on'
        ]


class TransportMovementSerializer(BaseEnterpriseAuditSerializer):

    class Meta:
        model = TransportMovement
        fields = [
            'id', 'vehicle', 'driver', 'origin', 'destination', 'departure_time',
            'arrival_time', 'transit_data', 'distance_covered', 'created_by',
            'updated_by','created_on', 'updated_on'
        ]
