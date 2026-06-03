from django.shortcuts import render
from rest_framework import viewsets

from common.mixins import BaseEnterpriseViewSet
from common.permissions.base import EnterpriseObjectLevelPermissionMixin
from ipss.models import PackagedProduct
from ipss.serializers import PackagedProductSerializers

# Create your views here.


class PackagedProductViewSet(
    EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet
):
    queryset = PackagedProduct.objects.select_related("session", "variant_ref").all()
    serializer_class = PackagedProductSerializers
