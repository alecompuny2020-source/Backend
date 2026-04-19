from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views as v

router = DefaultRouter()

router.register(r'departments', v.DepartmentViewSet, basename='departments')
router.register(r'next_of_kins', v.NextOfKinsViewSet, basename='kins')
router.register(r'ids', v.UserIdentityViewSet, basename='identity')

urlpatterns = [
    path("", include(router.urls))
]
