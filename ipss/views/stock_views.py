from django.shortcuts import render
from ipss.models import ProductStock, StockMovement
from common.permissions.base import EnterpriseObjectLevelPermissionMixin
from common.mixins import BaseEnterpriseViewSet
from rest_framework import viewsets
from ipss.serializers import (ProductStockSerializers,
StockMovementSerializers)

# Create your views here.


class ProductStockViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = ProductStock.objects.select_related('product_type', 'storage_unit').all()
    serializer_class = ProductStockSerializers


class StockMovementViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = StockMovement.objects.select_related('stock').all()
    serializer_class = StockMovementSerializers
