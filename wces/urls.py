from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views as v

router = DefaultRouter()


router.register(r"waste-categories", v.WasteCategoryViewSet, basename="waste_category")
router.register(
    r"waste-collection", v.WasteCollectionViewSet, basename="waste_collection"
)
router.register(r"disposal-areas", v.DisposalAreaViewSet, basename="area")
router.register(r"waste-outflow", v.WasteOutflowViewSet, basename="waste_outflow")

urlpatterns = [
    path("", include(router.urls)),
]
