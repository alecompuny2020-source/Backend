from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views as v

router = DefaultRouter()

router.register(r"farms", v.FarmViewSet)
router.register(r"manager-history", v.FarmManagerHistoryViewSet, basename="manager")
router.register(r"farm-sheds", v.FarmShedViewSet, basename="shed")
router.register(r"farm-blocks", v.FarmBlockViewSet, basename="block")
router.register(r"farm-batches", v.FarmBatchViewSet, basename="batch")
router.register(
    r"flock-observations", v.DailyObservationViewSet, basename="observation"
)
router.register(r"farm-flocks", v.BreederFlockViewSet, basename="flocks")
router.register(r"incubators", v.IncubatorViewSet, basename="incubator")
router.register(r"incubation-cycles", v.IncubationCycleViewSet, basename="cycle")
router.register(r"hatch-records", v.HatchRecordViewSet, basename="hatch")
router.register(r"health-protocols", v.HealthProtocolViewSet, basename="health")
router.register(r"medical-records", v.MedicalRecordViewSet, basename="medical_record")
router.register(r"disease-outbreaks", v.DiseaseOutbreakViewSet, basename="disease")
router.register(r"farm-vehicles", v.FarmVehicleViewSet, basename="vehicle")
router.register(
    r"transport-movements", v.TransportMovementViewSet, basename="transport"
)
router.register(
    r"crop-productions", v.CropProductionViewSet, basename="crop-production"
)
router.register(
    r"farm-ingredients", v.FeedIngredientStockViewSet, basename="ingredients"
)
router.register(r"ecological-inputs", v.EcologicalInputViewSet, basename="inputs")

urlpatterns = [
    path("", include(router.urls)),
]
