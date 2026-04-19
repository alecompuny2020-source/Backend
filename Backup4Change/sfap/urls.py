from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views as v

router = DefaultRouter()

router.register(r'farms', v.FarmViewSet, basename='farm')
router.register(r'sheds', v.FarmShedViewSet, basename = 'shed')
router.register(r'batches', v.FarmShedViewSet, basename = 'batch')
router.register(r'observations', v.DailyObservationViewSet, basename = 'observation')
router.register(r'flocks', v.BreederFlockViewSet, basename = 'flock')
router.register(r'incubators', v.IncubatorViewSet, basename = 'incubator')
router.register(r'incubation_cycles', v.IncubationCycleViewSet, basename = 'cycle')
router.register(r'hatch_records', v.HatchRecordViewSet, basename = 'hatch')
router.register(r'medical_protocals', v.HealthProtocolViewSet, basename = 'protocal')
router.register(r'medical_records', v.MedicalRecordViewSet, basename = 'record')
router.register(r'outbreaks', v.DiseaseOutbreakViewSet, basename = 'outbreak')
router.register(r'farm_vehicles', v.FarmVehicleViewSet, basename = 'vehicle')
router.register(r'farm_movements', v.TransportMovementViewSet, basename = 'movement')
router.register(r'farm_manager_histories', v.FarmManagerViewSet, basename = "farm_history")

urlpatterns = [
    path("", include(router.urls))
]
