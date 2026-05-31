from common.mixins import BaseEnterpriseViewSet
from common.permissions.base import EnterpriseObjectLevelPermissionMixin
from sfap.models import FarmVehicle, TransportMovement
from sfap.serializers import FarmVehicleSerializer, TransportMovementSerializer


class FarmVehicleViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = FarmVehicle.objects.all()
    serializer_class = FarmVehicleSerializer


class TransportMovementViewSet(
    EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet
):
    queryset = TransportMovement.objects.select_related("vehicle", "driver").all()
    serializer_class = TransportMovementSerializer
