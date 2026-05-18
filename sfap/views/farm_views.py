from django.shortcuts import render
from sfap.serializers import (FarmSerializers, FarmManagerHistorySerializer, FarmShedSerializer,
FarmBatchSerializer, DailyObservationSerializer, BreederFlockSerializer)
from sfap.models import Farm, ManagerHistory, FarmShed, Batch, DailyObservation, BreederFlock
from common.permissions.base import EnterpriseObjectLevelPermissionMixin
from common.mixins import BaseEnterpriseViewSet
from common.pagination import GenericEnteprisePaginator
from rest_framework import viewsets

# Create your views here.

class FarmViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = Farm.objects.all()
    serializer_class = FarmSerializers


class FarmManagerHistoryViewSet(EnterpriseObjectLevelPermissionMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ManagerHistory.objects.select_related('farm', 'plant', 'manager').all()
    serializer_class = FarmManagerHistorySerializer
    pagination_class = GenericEnteprisePaginator


class FarmShedViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = FarmShed.objects.select_related('farm').all()
    serializer_class = FarmShedSerializer


class FarmBatchViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = Batch.objects.select_related('shed__farm').all()
    serializer_class = FarmBatchSerializer


class DailyObservationViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = DailyObservation.objects.select_related('batch').all()
    serializer_class = DailyObservationSerializer


class BreederFlockViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = BreederFlock.objects.select_related('source_batch').all()
    serializer_class = BreederFlockSerializer
