from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views as v

router = DefaultRouter()

router.register(r"warehouses", v.WarehouseLocationViewSet)
router.register(r"zones", v.ZoneViewSet)
router.register(r"storage-units", v.StorageUnitViewSet)
router.register(r"products", v.ProductViewSet)
router.register(r"product-variants", v.ProductVariantViewSet, basename="variants")
router.register(r"product-stocks", v.ProductStockViewSet, basename="stock")
router.register(r"product-movements", v.StockMovementViewSet, basename="movement")

urlpatterns = [
    path("", include(router.urls)),
]
