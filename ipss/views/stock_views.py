from django.shortcuts import render
from rest_framework import viewsets

from common.mixins import BaseEnterpriseViewSet
from common.permissions.base import EnterpriseObjectLevelPermissionMixin
from ipss.models import ProductStock, StockMovement
from ipss.serializers import ProductStockSerializers, StockMovementSerializers

# Create your views here.


class ProductStockViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = ProductStock.objects.select_related("product_type", "storage_unit").all()
    serializer_class = ProductStockSerializers


class StockMovementViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = StockMovement.objects.select_related("stock").all()
    serializer_class = StockMovementSerializers
