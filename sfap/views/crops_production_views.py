from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets
from rest_framework.decorators import action

from common.mixins import BaseEnterpriseViewSet
from common.pagination import GenericEnteprisePaginator
from common.permissions.base import EnterpriseObjectLevelPermissionMixin
from common.services import CropsManagementService
from sfap.models import CropProduction, EcologicalInput, FeedIngredientStock
from sfap.serializers import (
    CropProductionSerializer,
    EcologicalInputSerializer,
    FeedIngredientStockSerializer,
    LogCropHarvestSerializer,
)


class CropProductionViewSet(
    EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet
):
    """
    ViewSet ya kudhibiti mzunguko mzima wa uzalishaji wa mazao (Crop Production).
    """

    queryset = CropProduction.objects.select_related("block").all()
    serializer_class = CropProductionSerializer

    @action(
        detail=True,
        methods=["post"],
        serializer_class=LogCropHarvestSerializer,
        url_path="log-harvest",
    )
    def log_harvest(self, request, pk=None):
        """
        Endpoint ya kurekodi mavuno ya zao husika na kuhamishia ghalani kama chakula cha kuku.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        actual_yield = serializer.validated_data["actual_yield_kg"]
        unit_cost = serializer.validated_data["unit_cost_tzs"]

        try:
            stock = CropsManagementService.process_harvest_to_feed_stock(
                crop_production_id=pk,
                actual_yield=actual_yield,
                unit_cost_tzs=unit_cost,
            )
            return Response(
                _("Mavuno yamefanikiwa kurekodiwa na stoki ya chakula imeongezwa.")
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class EcologicalInputViewSet(
    EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet
):
    queryset = EcologicalInput.objects.select_related("origin").all()
    serializer_class = EcologicalInputSerializer


class FeedIngredientStockViewSet(
    EnterpriseObjectLevelPermissionMixin, viewsets.ReadOnlyModelViewSet
):
    queryset = FeedIngredientStock.objects.select_related("farm").all()
    serializer_class = FeedIngredientStockSerializer
    pagination_class = GenericEnteprisePaginator
