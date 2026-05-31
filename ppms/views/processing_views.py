from django.shortcuts import render
from common.permissions.base import EnterpriseObjectLevelPermissionMixin
from common.mixins import BaseEnterpriseViewSet
from ppms.serializers import ProcessingPlantSerializers
from ppms.models import ProcessingPlant

# Create your views here.

class ProcessingPlantViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = ProcessingPlant.objects.select_related('plant_manager').all()
    serializer_class = ProcessingPlantSerializers
