from django.contrib.postgres.indexes import GinIndex
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from common.mixins import BaseEnterpriseAuditModelMixin


class FarmVehicle(BaseEnterpriseAuditModelMixin):
    """
    Tracks trucks, tractors, and bikes.
    Essential for fuel tracking and maintenance scheduling.
    """

    plate_number = models.CharField(_("Plate Number"), max_length=20, unique=True)
    vehicle_type = models.ForeignKey("core.FarmVehicleType", on_delete=models.RESTRICT)
    # vehicle_type = models.CharField(
    #     _("Type"), max_length=50
    # )  # e.g., Refrigerated Truck, Feed Loader
    max_payload_kg = models.PositiveIntegerField(_("Max Payload (KG)"))

    # Blueprint for vehicle_specs:
    # {
    #   "last_service_km": 15000,
    #   "fuel_type": "Diesel",
    #   "has_gps": true,
    #   "refrigeration_specs": {"min_temp": -20, "max_temp": 4}
    # }
    vehicle_specs = models.JSONField(
        _("Vehicle Specifications"), default=dict, blank=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "farm_vehicle"
        verbose_name = _("Farm Vehicle")
        verbose_name_plural = _("Farm Vehicles")
        indexes = [
            GinIndex(fields=["vehicle_specs"], name="vehicle_specs_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Farm Vehicle '{self.plate_number}' "
                f"from: {old_data} to: "
                f"{{'type': '{self.vehicle_type}', 'payload': {self.max_payload_kg}kg, 'specs': {self.vehicle_specs}}}"
            )
        return (
            f"Registered Farm Vehicle '{self.plate_number}' "
            f"({self.vehicle_type}, Max Payload: {self.max_payload_kg}kg)"
        )


class TransportMovement(BaseEnterpriseAuditModelMixin):
    """Tracks the journey of assets (Birds, Feed, or Meat)."""

    vehicle = models.ForeignKey(FarmVehicle, on_delete=models.PROTECT)
    driver = models.ForeignKey("hrms.Employee", on_delete=models.PROTECT)
    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField(null=True, blank=True)

    # Blueprint for transit_data:
    # {
    #   "cargo_type": "LIVE_CHICKS",
    #   "item_count": 5000,
    #   "disinfection_done": true,
    #   "temp_at_arrival": 22.5,
    #   "mortality_during_transit": 2
    # }
    transit_data = models.JSONField(_("Transit Audit Data"), default=dict)

    class Meta:
        db_table = "transport_movement"
        verbose_name = _("Transport Movement")
        verbose_name_plural = _("Transport Movements")
        indexes = [
            GinIndex(fields=["transit_data"], name="transit_data_gin_idx"),
        ]

    @property
    def distance_covered(self) -> float:
        if self.end_odometer and self.start_odometer:
            return self.end_odometer - self.start_odometer
        return 0

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Transport Movement for Vehicle '{self.vehicle.plate_number}' "
                f"from: {old_data} to: origin {self.origin}, destination {self.destination}, "
                f"cargo {self.transit_data.get('cargo_type')}, count {self.transit_data.get('item_count')}"
            )
        if self.arrival_time:
            return (
                f"Transport Movement completed for Vehicle '{self.vehicle.plate_number}' "
                f"from {self.origin} to {self.destination}, cargo {self.transit_data.get('cargo_type')}, "
                f"count {self.transit_data.get('item_count')}, arrived at {self.arrival_time}"
            )
        return (
            f"Transport Movement initiated for Vehicle '{self.vehicle.plate_number}' "
            f"from {self.origin} to {self.destination}, cargo {self.transit_data.get('cargo_type')}, "
            f"count {self.transit_data.get('item_count')}, departed at {self.departure_time}"
        )

    def clean(self):
        """Ensure cargo doesn't exceed vehicle capacity."""
        cargo_weight = self.transit_data.get("total_weight_kg", 0)
        if cargo_weight > self.vehicle.max_payload_kg:
            raise ValidationError(
                _(
                    f"Overload Alert: Cargo weight ({cargo_weight}kg) "
                    f"exceeds vehicle capacity ({self.vehicle.max_payload_kg}kg)."
                )
            )

        if self.arrival_time and self.arrival_time < self.departure_time:
            raise ValidationError(_("Arrival time cannot be before departure time."))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.vehicle.plate_number}: {self.origin} -> {self.destination}"
