from django.shortcuts import render
from common.permissions.base import EnterpriseObjectLevelPermissionMixin
from common.mixins import BaseEnterpriseViewSet
from wces.models import DisposalArea, WasteOutflow
from wces.serializers import DisposalAreaSerializers, WasteOutflowSerializers

# Create your views here.

class DisposalAreaViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = DisposalArea.objects.all()
    serializer_class = DisposalAreaSerializers


class WasteOutflowViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = WasteOutflow.objects.select_related('collection_logs', 'destination').all()
    serializer_class = WasteOutflowSerializers
