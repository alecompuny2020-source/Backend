from django.shortcuts import render
from rest_framework import viewsets

from common.mixins import BaseEnterpriseViewSet
from common.permissions.base import EnterpriseObjectLevelPermissionMixin
from ipss.models import StorageUnit, WarehouseLocation, Zone
from ipss.serializers import (
    StorageUnitSerializers,
    WarehouseLocationSerializers,
    ZoneSerializers,
)

# Create your views here.


class WarehouseLocationViewSet(
    EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet
):
    queryset = WarehouseLocation.objects.all()
    serializer_class = WarehouseLocationSerializers


class ZoneViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = Zone.objects.select_related("warehouse").all()
    serializer_class = ZoneSerializers


class StorageUnitViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = StorageUnit.objects.select_related("zone", "zone__warehouse").all()
    serializer_class = StorageUnitSerializers
