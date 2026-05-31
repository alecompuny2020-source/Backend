from django.shortcuts import render
from rest_framework import viewsets

from common.mixins import BaseEnterpriseViewSet
from common.permissions.base import EnterpriseObjectLevelPermissionMixin
from fns.models import FeedInventory
from fns.serializers import FeedInventorySerializer

# Create your views here.


class FeedInventoryViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = FeedInventory.objects.select_related("feed_type").all()
    serializer_class = FeedInventorySerializer
