from django.shortcuts import render
from ipss.models import PackagedProduct
from common.permissions.base import EnterpriseObjectLevelPermissionMixin
from common.mixins import BaseEnterpriseViewSet
from rest_framework import viewsets
from ipss.serializers import PackagedProductSerializers

# Create your views here.


class PackagedProductViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = PackagedProduct.objects.select_related('session', 'variant_ref').all()
    serializer_class = PackagedProductSerializers
