from sfap.serializers import (IncubatorSerializer, IncubationCycleSeializer, HatchRecordSerializer)
from common.mixins import BaseEnterpriseViewSet
from sfap.models import Incubator, IncubationCycle, HatchRecord
from common.permissions.base import EnterpriseObjectLevelPermissionMixin


class IncubatorViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = Incubator.objects.all()
    serializer_class = IncubatorSerializer


class IncubationCycleViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = IncubationCycle.objects.select_related('breeder_flock', 'hatcher').all()
    serializer_class = IncubationCycleSeializer


class HatchRecordViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = HatchRecord.objects.select_related('incubation_cycle', 'destination_batch').all()
    serializer_class = HatchRecordSerializer
