from django.shortcuts import render
from common.permissions.base import EnterpriseObjectLevelPermissionMixin
from common.mixins import BaseEnterpriseViewSet
from wces.models import WasteCategory, WasteCollection
from wces.serializers import WasteCategorySerializers, WasteCollectionSerializers

# Create your views here.

class WasteCategoryViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = WasteCategory.objects.all()
    serializer_class = WasteCategorySerializers


class WasteCollectionViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = WasteCollection.objects.select_related('location', 'category', 'source_batch').all()
    serializer_class = WasteCollectionSerializers
