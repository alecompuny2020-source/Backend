from common.mixins import BaseEnterpriseViewSet
from common.permissions.base import EnterpriseObjectLevelPermissionMixin
from sfap.models import HatchRecord, IncubationCycle, Incubator
from sfap.serializers import (
    HatchRecordSerializer,
    IncubationCycleSeializer,
    IncubatorSerializer,
)


class IncubatorViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = Incubator.objects.all()
    serializer_class = IncubatorSerializer


class IncubationCycleViewSet(
    EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet
):
    queryset = IncubationCycle.objects.select_related("breeder_flock", "hatcher").all()
    serializer_class = IncubationCycleSeializer


class HatchRecordViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = HatchRecord.objects.select_related(
        "incubation_cycle", "destination_batch"
    ).all()
    serializer_class = HatchRecordSerializer
