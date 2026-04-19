from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views as v

router = DefaultRouter()

router.register(r'feed_types', v.FeedTypeViewSet, basename='feed')
router.register(r'feed_inventories', v.FeedInventoryViewSet, basename='inventory')
router.register(r'feed_consumptions', v.FeedConsumptionViewSet, basename='consumption')

urlpatterns = [
    path("", include(router.urls))
]
