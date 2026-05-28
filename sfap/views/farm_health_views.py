from sfap.serializers import (HealthProtocolSerializer, MedicalRecordSerializer, DiseaseOutbreakSerializer)
from common.mixins import BaseEnterpriseViewSet
from sfap.models import HealthProtocol, MedicalRecord, DiseaseOutbreak
from common.permissions.base import EnterpriseObjectLevelPermissionMixin


class HealthProtocolViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = HealthProtocol.objects.all()
    serializer_class = HealthProtocolSerializer


class MedicalRecordViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = MedicalRecord.objects.select_related('batch').all()
    serializer_class = MedicalRecordSerializer


class DiseaseOutbreakViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = DiseaseOutbreak.objects.select_related('batch').all()
    serializer_class = DiseaseOutbreakSerializer
