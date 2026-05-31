from django.shortcuts import render

from common.mixins import BaseEnterpriseViewSet
from common.permissions.base import EnterpriseObjectLevelPermissionMixin
from ppms.models import ProcessingPlant, ProcessingSession
from ppms.serializers import ProcessingPlantSerializers, ProcessingSessionSerializers

# Create your views here.


class ProcessingPlantViewSet(
    EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet
):
    queryset = ProcessingPlant.objects.select_related("plant_manager").all()
    serializer_class = ProcessingPlantSerializers


class ProcessingSessionViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = ProcessingSession.objects.select_related('plant', 'source_batch', 'assigned_workers').all()
    serializer_class = ProcessingSessionSerializers
