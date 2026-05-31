from django.shortcuts import render
from rest_framework import viewsets

from common.mixins import BaseEnterpriseViewSet
from common.permissions.base import EnterpriseObjectLevelPermissionMixin
from fns.models import FeedType
from fns.serializers import FeedTypeSerializer

# Create your views here.


class FeedTypeViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = FeedType.objects.all()
    serializer_class = FeedTypeSerializer
