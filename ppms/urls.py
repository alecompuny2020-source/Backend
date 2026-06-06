from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views as v

router = DefaultRouter()

router.register(r"processing-plants", v.ProcessingPlantViewSet, basename = "plant")
router.register(r"processing-sessions", v.ProcessingSessionViewSet, basename="sessions")

urlpatterns = [
    path("", include(router.urls)),
]
