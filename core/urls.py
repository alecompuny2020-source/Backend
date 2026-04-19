from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views as v

router = DefaultRouter()

router.register(r'', v.AuthViewSet, basename='auth')

urlpatterns = [
    path("", include(router.urls)),
    path('token/refresh/', TokenRefreshView.as_view()),
]
