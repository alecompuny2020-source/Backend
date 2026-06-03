from django.shortcuts import render
from ipss.models import Product, ProductVariant
from common.permissions.base import EnterpriseObjectLevelPermissionMixin
from common.mixins import BaseEnterpriseViewSet
from rest_framework import viewsets
from ipss.serializers import (ProductSerializers,
ProductVariantSerializers)

# Create your views here.


class ProductViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializers


class ProductVariantViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = ProductVariant.objects.select_related('product').all()
    serializer_class = ProductVariantSerializers
