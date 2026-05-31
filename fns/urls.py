from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views as v

router = DefaultRouter()

router.register(r"farms", v.FeedTypeViewSet, basename="feed_type")
router.register(r"farm-inventories", v.FeedInventoryViewSet, basename="inventory")
router.register(r"farm-consumptions", v.FeedTypeViewSet, basename="consumption")

urlpatterns = [
    path("", include(router.urls)),
]
