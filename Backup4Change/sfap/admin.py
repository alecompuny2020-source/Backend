from django.contrib import admin
from .models import (Farm,
ManagerHistory,
FarmShed,
Batch,
DailyObservation,
BreederFlock,
Incubator,
IncubationCycle,
HatchRecord,
FarmVehicle,
TransportMovement,
HealthProtocol,
MedicalRecord,
DiseaseOutbreak)
from guardian.admin import GuardedModelAdmin

# Register your models here.

# admin.site.register(Farm)
@admin.register(Farm)
class FarmAdmin(GuardedModelAdmin):
    list_display = ('name', 'created_by', 'is_active')

admin.site.register(ManagerHistory)
admin.site.register(FarmShed)
admin.site.register(Batch)
admin.site.register(DailyObservation)
admin.site.register(BreederFlock)
admin.site.register(Incubator)
admin.site.register(IncubationCycle)
admin.site.register(HatchRecord)
admin.site.register(FarmVehicle)
admin.site.register(TransportMovement)
admin.site.register(HealthProtocol)
admin.site.register(MedicalRecord)
admin.site.register(DiseaseOutbreak)
