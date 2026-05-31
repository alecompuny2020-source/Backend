from common.mixins import BaseEnterpriseViewSet
from common.permissions.base import EnterpriseObjectLevelPermissionMixin
from sfap.models import DiseaseOutbreak, HealthProtocol, MedicalRecord
from sfap.serializers import (
    DiseaseOutbreakSerializer,
    HealthProtocolSerializer,
    MedicalRecordSerializer,
)


class HealthProtocolViewSet(
    EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet
):
    queryset = HealthProtocol.objects.all()
    serializer_class = HealthProtocolSerializer


class MedicalRecordViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = MedicalRecord.objects.select_related("batch").all()
    serializer_class = MedicalRecordSerializer


class DiseaseOutbreakViewSet(
    EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet
):
    queryset = DiseaseOutbreak.objects.select_related("batch").all()
    serializer_class = DiseaseOutbreakSerializer
