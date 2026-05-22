from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views as v

router = DefaultRouter()

router.register(r'farms', v.FarmViewSet)
router.register(r'manager-history', v.FarmManagerHistoryViewSet, basename = 'manager')
router.register(r'farm-sheds', v.FarmShedViewSet, basename = 'shed')
router.register(r'farm-blocks', v.FarmBlockViewSet, basename = 'block')
router.register(r'farm-batches', v.FarmBatchViewSet, basename = 'batch')
router.register(r'flock-observations', v.DailyObservationViewSet, basename = 'observation')
router.register(r'farm-flocks', v.BreederFlockViewSet, basename = 'flocks')
router.register(r'incubators', v.IncubatorViewSet, basename = 'incubator')
router.register(r'incubation-cycle', v.IncubationCycleViewSet, basename = 'cycle')
router.register(r'hatch-records', v.HatchRecordViewSet, basename = 'hatch')

urlpatterns = [
    path("", include(router.urls)),
]
