from django.shortcuts import render

from common.mixins import BaseEnterpriseViewSet
from common.permissions.base import EnterpriseObjectLevelPermissionMixin
from ppms.models import ProcessingPlant
from ppms.serializers import ProcessingPlantSerializers

# Create your views here.


class ProcessingPlantViewSet(
    EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet
):
    queryset = ProcessingPlant.objects.select_related("plant_manager").all()
    serializer_class = ProcessingPlantSerializers
