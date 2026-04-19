from django.db import models
import uuid
from django.contrib.postgres.indexes import GinIndex
from django.utils.translation import gettext_lazy as _
from ..helpers import BOOKING_STATUS_CHOICES
from ..utils import FarmAuditBaseModel

# Create your models here.

class VehicleModel(models.Model):
    """
    VEHICLE SPECIFICATIONS (Normalized from size_X/size_XL)
    Acts as a blueprint for different types of transport assets.
    """

    model_id = models.CharField(primary_key=True, max_length=15)
    make = models.CharField(max_length=50)
    model_name = models.CharField(max_length=50)
    year = models.IntegerField()
    capacity = models.IntegerField()
    v_type = models.CharField(
        max_length=20, help_text=_("Ride, Delivery, Tractor, etc.")
    )

    class Meta:
        db_table = "vehicle_model"

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Vehicle Model '{self.make} {self.model_name}' "
                f"from: {old_data} to: year {self.year}, capacity {self.capacity}, type {self.v_type}"
            )
        return (
            f"Created Vehicle Model '{self.make} {self.model_name}' "
            f"({self.year}, capacity {self.capacity}, type {self.v_type})"
        )

    def clean(self):
        """Validate production year."""
        current_year = timezone.now().year
        if self.year > current_year + 1:
            raise ValidationError(_("Vehicle year cannot be in the future."))

    def __str__(self):
        return f"{self.make} {self.model_name} ({self.year})"


class Vehicle(FarmAuditBaseModel):
    """
    FLEET REGISTRY (VYOMBO VYA MOTO)
    Tracks physical assets and their ownership.
    """

    vid = models.CharField(primary_key=True, max_length=15)
    license_plate = models.CharField(max_length=15, unique=True)
    model = models.ForeignKey(VehicleModel, on_delete=models.PROTECT)

    # Soft Link to Identity Vault (User/Owner)
    owner_id = models.PositiveIntegerField(db_index=True)

    current_condition = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "vehicle"

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Vehicle '{self.license_plate}' "
                f"from: {old_data} to: model {self.model.model_name}, condition {self.current_condition}, active {self.is_active}"
            )
        return (
            f"Registered Vehicle '{self.license_plate}' "
            f"model {self.model.model_name}, condition {self.current_condition}, active {self.is_active}"
        )

    def __str__(self):
        return f"{self.license_plate} - {self.model.model_name}"


class Driver(models.Model):
    """
    DRIVER REGISTRY
    Operational details for service providers.
    """

    # Soft Link to Identity Vault (User)
    driver_id = models.PositiveIntegerField(primary_key=True)
    license_no = models.CharField(max_length=50)
    expiry_date = models.DateField()
    avg_rating = models.DecimalField(max_digits=3, decimal_places=1, default=5.0)
    is_available = models.BooleanField(default=False)

    # Real-time Telemetry (for the Geospatial Dispatcher)
    # Stores {"lat": -6.7, "lng": 39.2, "last_updated": "..."}
    current_telemetry = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "driver"
        indexes = [
            GinIndex(fields=["current_telemetry"], name="current_telemetry_gin_idx")
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Driver {self.driver_id} "
                f"from: {old_data} to: license {self.license_no}, expiry {self.expiry_date}, available {self.is_available}"
            )
        return (
            f"Registered Driver {self.driver_id} "
            f"license {self.license_no}, expiry {self.expiry_date}, available {self.is_available}"
        )

    @property
    def has_valid_license(self):
        """HELPER: Checks if the license is currently valid."""
        return self.expiry_date >= timezone.now().date()

    def clean(self):
        """Safety Validation: An expired driver cannot be marked as available."""
        if self.is_available and not self.has_valid_license:
            raise ValidationError(
                _("Cannot set driver to available; license has expired.")
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class MobilityBooking(FarmAuditBaseModel):
    """
    THE UNIVERSAL BOOKING TABLE
    Tracks the lifecycle of a movement request (Bolt-style).
    """

    booking_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Who and Where (Soft Links)
    requester_id = models.PositiveIntegerField(db_index=True)
    asset_type = models.CharField(max_length=20)  # FARM, BUILDING, UNIT
    asset_id = models.PositiveIntegerField()

    # Request Details
    booking_type = models.CharField(max_length=20)  # RIDE, DELIVERY, RENTAL
    pickup_loc = models.CharField(max_length=255)
    dropoff_loc = models.CharField(max_length=255)
    request_time = models.DateTimeField(auto_now_add=True)

    # Assignment (Physical links within the same vault)
    assigned_driver = models.ForeignKey(
        Driver, on_delete=models.SET_NULL, null=True, blank=True
    )
    assigned_vehicle = models.ForeignKey(
        Vehicle, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Point #8: Tracking & Metadata (JSONB + GIN)
    # Stores: {"path": [...], "actual_distance": 12.5, "cargo": {"type": "Poultry", "qty": 500}}
    telemetry_data = models.JSONField(default=dict, blank=True)
    cargo_details = models.JSONField(default=dict, blank=True)

    status = models.CharField(
        max_length=20, choices=BOOKING_STATUS_CHOICES, default="PENDING"
    )

    class Meta:
        db_table = "mobility_booking"
        indexes = [
            GinIndex(fields=["telemetry_data"], name="mb_telemetry_gin_idx"),
            GinIndex(fields=["cargo_details"], name="mb_cargo_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Mobility Booking '{self.booking_id}' "
                f"from: {old_data} to: status {self.status}, "
                f"pickup {self.pickup_loc}, dropoff {self.dropoff_loc}"
            )
        if self.status == "COMPLETED":
            return (
                f"Mobility Booking '{self.booking_id}' completed — "
                f"pickup {self.pickup_loc}, dropoff {self.dropoff_loc}, "
                f"driver {self.assigned_driver.driver_id if self.assigned_driver else 'N/A'}, "
                f"vehicle {self.assigned_vehicle.license_plate if self.assigned_vehicle else 'N/A'}"
            )
        return (
            f"Created Mobility Booking '{self.booking_id}' "
            f"type {self.booking_type}, pickup {self.pickup_loc}, dropoff {self.dropoff_loc}, "
            f"status {self.status}"
        )

    def clean(self):
        """
        Cross-Model Validation: Ensure vehicle and driver are eligible for dispatch.
        """
        if self.status == "ASSIGNED":
            if not self.assigned_driver or not self.assigned_vehicle:
                raise ValidationError(
                    _("An 'ASSIGNED' booking must have both a driver and a vehicle.")
                )

            if not self.assigned_driver.has_valid_license:
                raise ValidationError(_("Assigned driver has an expired license."))

            if not self.assigned_vehicle.is_active:
                raise ValidationError(
                    _(
                        "Assigned vehicle is currently marked as inactive/under maintenance."
                    )
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class TripLedger(models.Model):
    """
    TRIP LEDGER (Financial Results)
    """

    ledger_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(MobilityBooking, on_delete=models.CASCADE)
    base_fare = models.DecimalField(max_digits=10, decimal_places=2)
    distance_fare = models.DecimalField(max_digits=10, decimal_places=2)
    surge_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)
    total_fare = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, default="UNPAID")

    class Meta:
        db_table = "trip_ledger"

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Trip Ledger for Booking '{self.booking.booking_id}' "
                f"from: {old_data} to: total fare {self.total_fare}, payment {self.payment_status}"
            )
        return (
            f"Created Trip Ledger for Booking '{self.booking.booking_id}' "
            f"base fare {self.base_fare}, distance fare {self.distance_fare}, "
            f"surge {self.surge_multiplier}, total {self.total_fare}, payment {self.payment_status}"
        )

    def save(self, *args, **kwargs):
        """Auto-calculate total fare on save."""
        self.total_fare = self.base_fare + (self.distance_fare * self.surge_multiplier)
        super().save(*args, **kwargs)


class MobilityRating(models.Model):
    """
    RATING & FEEDBACK
    """

    booking = models.OneToOneField(
        MobilityBooking, on_delete=models.CASCADE, primary_key=True
    )
    driver_rating = models.IntegerField()
    passenger_rating = models.IntegerField()
    feedback_text = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "mobility_rating"

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Mobility Rating for Booking '{self.booking.booking_id}' "
                f"from: {old_data} to: driver rating {self.driver_rating}, passenger rating {self.passenger_rating}"
            )
        return (
            f"Recorded Mobility Rating for Booking '{self.booking.booking_id}' "
            f"driver rating {self.driver_rating}, passenger rating {self.passenger_rating}, "
            f"feedback: {self.feedback_text or 'N/A'}"
        )
