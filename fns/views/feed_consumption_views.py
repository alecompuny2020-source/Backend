from django.shortcuts import render
from rest_framework import viewsets

from common.mixins import BaseEnterpriseViewSet
from common.permissions.base import EnterpriseObjectLevelPermissionMixin
from fns.models import FeedConsumption
from fns.serializers import FeedConsumptionSerializer

# Create your views here.


class FeedTypeViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = FeedConsumption.objects.select_related("batch", "feed_type").all()
    serializer_class = FeedConsumptionSerializer
