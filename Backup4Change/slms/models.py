from django.db import models, transaction
import random
from decimal import Decimal
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.db.models import F, Q, Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from ..helpers import CARRIER_TYPES, RATE_TYPES, SHIPPING_CHOICES
from ..utils import FarmAuditBaseModel

# Create your models here.

class ShipmentRequest(models.Model):
    """
    Initial request to fulfill a Sales Order.
    Acts as the bridge between the Sales Team and the Warehouse.
    """

    order = models.OneToOneField(
        "core.Order", on_delete=models.CASCADE, related_name="shipment_request"
    )
    requested_at = models.DateTimeField(default=timezone.now)
    is_fulfilled = models.BooleanField(default=False)

    class Meta:
        db_table = "shipment_request"
        verbose_name = _("Shipment Request")

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Shipment Request for Order '{self.order.order_number}' "
                f"from: {old_data} to: fulfilled {self.is_fulfilled}"
            )
        return (
            f"Created Shipment Request for Order '{self.order.order_number}' "
            f"requested at {self.requested_at}, fulfilled {self.is_fulfilled}"
        )

    def __str__(self):
        return f"Request: {self.order.order_id}"


class Shipment(models.Model):
    """
    Tracks physical fulfillment and logistics performance.
    Includes security (OTP) and carrier assignment.
    """

    request = models.ForeignKey(
        ShipmentRequest, on_delete=models.CASCADE, related_name="shipments"
    )
    tracking_number = models.CharField(max_length=100, unique=True, db_index=True)
    status = models.CharField(
        max_length=20, choices=SHIPPING_CHOICES, default="REQUESTED"
    )
    vehicle_registration = models.CharField(_("Vehicle ID"), max_length=50, blank=True)

    # Responsible Staff & Carriers
    assigned_staff = models.ForeignKey(
        settings.FARM_WORKER,
        on_delete=models.SET_NULL,
        null=True,
        related_name="prepared_shipments",
    )
    logistic_agent = models.ForeignKey(
        settings.FARM_WORKER,
        on_delete=models.SET_NULL,
        null=True,
        related_name="carrier_shipments",
    )
    calculated_cost = MoneyField(
        verbose_name=_("Calculated Cost"),
        max_digits=15,
        decimal_places=2,
        default_currency="TZS",
    )

    dispatched_at = models.DateTimeField(default=timezone.now)
    delivered_at = models.DateTimeField(null=True, blank=True)
    delivery_otp = models.CharField(max_length=6, blank=True, null=True)

    # Blueprint for shipment_metadata:
    # Combined Metadata (Trip data + Proof of Delivery)
    # Blueprint:
    # {
    #   "start_odo": 1200, "end_odo": 1245, "fuel_spent": 5000,
    #   "signed_by": "John Doe", "photo_url": "s3://...", "temp_at_arrival": "4°C"
    # }
    # {
    #   "vehicle_plate": "T 442 DFG",
    #   "driver_phone": "+255...",
    #   "carrier_service_type": "Express",
    #   "delivery_notes": "Leave at gate if no answer"
    # }
    shipment_metadata = models.JSONField(
        _("Shipment Metadata"), default=dict, blank=True
    )

    class Meta:
        db_table = "shipment"
        verbose_name = _("Shipment")
        ordering = ["-dispatched_at"]
        indexes = [
            GinIndex(fields=["shipment_metadata"], name="shipment_meta_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Shipment '{self.tracking_number}' "
                f"from: {old_data} to: status {self.status}, vehicle {self.vehicle_registration}, "
                f"assigned staff {self.assigned_staff}, logistic agent {self.logistic_agent}"
            )
        if self.status == "DELIVERED" and self.delivered_at:
            return (
                f"Shipment '{self.tracking_number}' delivered at {self.delivered_at}, "
                f"vehicle {self.vehicle_registration}, signed by {self.shipment_metadata.get('signed_by')}"
            )
        return (
            f"Shipment '{self.tracking_number}' created for Request '{self.request.id}' "
            f"status {self.status}, vehicle {self.vehicle_registration}, cost {self.calculated_cost}"
        )

    def clean(self):
        """Security: Prevent delivering without an OTP if status is set to DELIVERED."""
        if self.status == "DELIVERED" and self.delivery_otp:
            raise ValidationError(
                _(
                    "Shipment cannot be marked DELIVERED until the OTP is cleared/verified."
                )
            )

    def update_status(self, new_status, description="", location=""):
        """Atomic update with history log."""
        with transaction.atomic():
            self.status = new_status
            if new_status == "DELIVERED":
                self.delivered_at = timezone.now()
                self.delivery_otp = None
            self.save()

            ShipmentStatusHistory.objects.create(
                shipment=self,
                status=new_status,
                description=description,
                location=location,
            )

    def generate_otp(self):
        """Generates 4-digit security code for delivery verification."""
        self.delivery_otp = str(random.randint(1000, 9999))
        self.save(update_fields=["delivery_otp"])
        return self.delivery_otp


class ShipmentStatusHistory(models.Model):
    """Granular audit trail for logistics."""

    shipment = models.ForeignKey(
        Shipment, on_delete=models.CASCADE, related_name="history"
    )
    status = models.CharField(max_length=20, choices=SHIPPING_CHOICES)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def get_log_message(self, old_data=None):
        return (
            f"Shipment '{self.shipment.tracking_number}' status updated to {self.status} "
            f"at {self.created_at}, location '{self.location}', description: {self.description}"
        )


class ShipmentLineItem(models.Model):
    """Links physical order items to a specific shipment box."""

    shipment = models.ForeignKey(
        Shipment, on_delete=models.CASCADE, related_name="line_items"
    )
    order_item = models.ForeignKey(
        settings.STOCK_PRODUCT_REFERENCE, on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField()
    weight_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    @property
    def total_weight(self):
        return self.quantity * (self.weight_kg or 0)

    def get_log_message(self, old_data=None):
        return (
            f"Added Line Item to Shipment '{self.shipment.tracking_number}' "
            f"product {self.order_item}, quantity {self.quantity}, total weight {self.total_weight}kg"
        )


class ShippingZone(FarmAuditBaseModel):
    """
    Defines geographical pricing areas.
    Crucial for differentiating delivery costs in Dodoma vs. Mwanza vs. London.
    """

    name = models.CharField(max_length=100, unique=True)
    post_code = models.CharField(max_length=10, null=True, blank=True)
    region = models.CharField(max_length=100, null=True)
    district = models.CharField(max_length=100, null=True)
    is_active = models.BooleanField(default=True)

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Shipping Zone '{self.name}' "
                f"from: {old_data} to: region {self.region}, district {self.district}, active {self.is_active}"
            )
        return (
            f"Created Shipping Zone '{self.name}' "
            f"region {self.region}, district {self.district}, active {self.is_active}"
        )

    def __str__(self):
        return f"{self.name} ({self.region})"


class ShippingMethod(FarmAuditBaseModel):
    """
    Stores different ways goods (like poultry or processed meat)
    can be transported from the farm to customers or plants.
    """

    name = models.CharField(_("Method Name"), max_length=100, unique=True)
    carrier_type = models.CharField(
        _("Carrier Type"), max_length=20, choices=CARRIER_TYPES, default="INTERNAL"
    )

    base_cost = MoneyField(
        _("Base Cost"),
        max_digits=15,
        decimal_places=2,
        default_currency="TZS",
        default=0,
    )

    estimated_delivery_time = models.CharField(
        _("Estimated Delivery Time"),
        max_length=100,
        blank=True,
        help_text=_("e.g., 2-4 hours, Next Day"),
    )

    is_active = models.BooleanField(_("Is Active"), default=True)

    # Blueprint for shipping_config:
    # {
    #    "max_weight_kg": 500,
    #    "refrigeration_required": true,
    #    "vehicle_type": "Motorcycle/Truck"
    # }
    shipping_config = models.JSONField(
        _("Technical Configuration"), default=dict, blank=True
    )

    class Meta:
        db_table = "logistics_shipping_method"
        verbose_name = _("Shipping Method")
        verbose_name_plural = _("Shipping Methods")
        ordering = ["name"]
        indexes = [
            GinIndex(fields=["shipping_config"], name="ship_method_cfg_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Shipping Method '{self.name}' "
                f"from: {old_data} to: carrier {self.carrier_type}, base cost {self.base_cost}, "
                f"config {self.shipping_config}"
            )
        return (
            f"Created Shipping Method '{self.name}' "
            f"carrier {self.carrier_type}, base cost {self.base_cost}, "
            f"delivery time {self.estimated_delivery_time}"
        )

    def validate_capacity(self, total_weight):
        """Checks if the weight exceeds method configuration limits."""
        max_weight = self.shipping_config.get("max_weight_kg")
        if max_weight and total_weight > Decimal(max_weight):
            return False
        return True

    def __str__(self):
        return f"{self.name} ({self.get_carrier_type_display()})"


class ShippingRate(models.Model):
    """
    Cost Logic: Calculates shipping price based on Weight and Zone.
    """

    method = models.ForeignKey("core.ShippingMethod", on_delete=models.CASCADE)
    zone = models.ForeignKey(ShippingZone, on_delete=models.CASCADE)
    cost = models.DecimalField(max_digits=12, decimal_places=2)
    rate_type = models.CharField(max_length=20, choices=RATE_TYPES, default="FLAT")

    min_weight = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_weight = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    class Meta:
        unique_together = ("method", "zone", "min_weight")

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Shipping Rate for Method '{self.method.name}' Zone '{self.zone.name}' "
                f"from: {old_data} to: cost {self.cost}, type {self.rate_type}, "
                f"weight range {self.min_weight}–{self.max_weight or '∞'}"
            )
        return (
            f"Created Shipping Rate for Method '{self.method.name}' Zone '{self.zone.name}' "
            f"cost {self.cost}, type {self.rate_type}, weight range {self.min_weight}–{self.max_weight or '∞'}"
        )

    def clean(self):
        if self.max_weight and self.min_weight >= self.max_weight:
            raise ValidationError(_("Min weight must be less than max weight."))
