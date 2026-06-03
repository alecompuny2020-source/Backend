from django.shortcuts import render
from ipss.models import WarehouseLocation, Zone, StorageUnit
from common.permissions.base import EnterpriseObjectLevelPermissionMixin
from common.mixins import BaseEnterpriseViewSet
from rest_framework import viewsets
from ipss.serializers import (WarehouseLocationSerializers,
ZoneSerializers,
StorageUnitSerializers)

# Create your views here.


class WarehouseLocationViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = WarehouseLocation.objects.all()
    serializer_class = WarehouseLocationSerializers


class ZoneViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = Zone.objects.select_related('warehouse').all()
    serializer_class = ZoneSerializers


class StorageUnitViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = StorageUnit.objects.select_related('zone', 'zone__warehouse').all()
    serializer_class = StorageUnitSerializers
