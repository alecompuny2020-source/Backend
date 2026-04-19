from django.db import models, transaction
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ..helpers import (CURRENCY_CHOICES, PRODUCT_CATEGORY_CHOICES,
                       READINESS_CHOICES, STOCK_MOVEMENT_TYPES,
                       STORAGE_UNIT_TYPES, UOM_CHOICES)
from ..utils import FarmAuditBaseModel


# Create your models here.


class Product(FarmAuditBaseModel):
    """
    Defines the global catalog (e.g., Broiler Meat, Organic Eggs).
    """

    name = models.CharField(_("Product Name"), max_length=100, unique=True)
    category = models.CharField(
        _("Category"), max_length=50, choices=PRODUCT_CATEGORY_CHOICES
    )

    source_batch = models.ForeignKey(
        settings.BATCH_REFERENCE,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resulting_stock",
    )

    # Stores grading, packaging, and specific storage requirements.
    # Blueprint for specs:
    # {
    #   "grade": "A",
    #   "weight_range": "50g-60g",
    #   "packaging_unit": "30-egg tray",
    #   "storage_requirement": "Refrigerated",
    #   pieces and divisions ()
    # }
    specs = models.JSONField(_("Product Specifications"), default=dict, blank=True)

    class Meta:
        db_table = "product"
        verbose_name = _("Product Type")
        indexes = [
            GinIndex(fields=["specs"], name="product_specs_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Product '{self.name}' "
                f"from: {old_data} to: category {self.category}, specs {self.specs}"
            )
        return (
            f"Created Product '{self.name}' "
            f"in category {self.get_category_display()}, specs {self.specs}"
        )

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class WarehouseLocation(FarmAuditBaseModel):
    """Physical facilities (e.g., Dodoma Main, Mwanza Staging)."""

    name = models.CharField(_("Location Name"), max_length=100, unique=True)
    code = models.CharField(_("Warehouse Code"), max_length=20, unique=True)
    address = models.CharField(
        _("Warehouse Address"),
        max_length=255,
    )
    is_active = models.BooleanField(default=True)

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Warehouse '{self.name}' "
                f"from: {old_data} to: code {self.code}, address {self.address}"
            )
        return (
            f"Created Warehouse '{self.name}' "
            f"(Code: {self.code}, Address: {self.address})"
        )

    def __str__(self):
        return f"{self.name} ({self.code})"


class Zone(FarmAuditBaseModel):
    """Sections like 'Cold Storage', 'Electronics', 'Cold Storage' or 'Loading Dock'."""

    warehouse = models.ForeignKey(
        WarehouseLocation, on_delete=models.CASCADE, related_name="zones"
    )
    name = models.CharField(_("Zone Name"), max_length=100)
    code = models.CharField(_("Zone Code"), max_length=10, blank=True)

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Zone '{self.name}' in Warehouse '{self.warehouse.name}' "
                f"from: {old_data} to: code {self.code}"
            )
        return (
            f"Created Zone '{self.name}' in Warehouse '{self.warehouse.name}' "
            f"(Code: {self.code})"
        )

    def __str__(self):
        return f"{self.warehouse.code} - {self.name}"


class StorageUnit(FarmAuditBaseModel):
    """The specific mean: Kabati, Shelf, Clipboard, Drawer, Shelf A1, Freezer 2, or Drawer 10."""

    zone = models.ForeignKey(
        Zone, on_delete=models.CASCADE, related_name="storage_units"
    )
    unit_code = models.CharField(_("Unit Code"), max_length=20)
    unit_type = models.CharField(
        _("Storage Mean"), max_length=20, choices=STORAGE_UNIT_TYPES, default="SHELF"
    )
    max_capacity = models.IntegerField(_("Max Capacity"), default=0)

    class Meta:
        unique_together = ("zone", "unit_code")

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Storage Unit '{self.unit_code}' in Zone '{self.zone.name}' "
                f"from: {old_data} to: type {self.unit_type}, capacity {self.max_capacity}"
            )
        return (
            f"Created Storage Unit '{self.unit_code}' in Zone '{self.zone.name}' "
            f"type {self.unit_type}, capacity {self.max_capacity}"
        )

    def __str__(self):
        return f"{self.get_unit_type_display()} {self.unit_code}"


class ProductStock(FarmAuditBaseModel):
    """
    Real-time inventory linking Production (Batch) to Sale (Revenue).
    Tracks readiness (Ready vs WIP) and physical storage (Kabati/Shelf).
    """

    product_type = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="current_stock"
    )
    storage_unit = models.ForeignKey(
        StorageUnit, on_delete=models.PROTECT, related_name="stock_items"
    )
    quantity_on_hand = models.DecimalField(
        _("Quantity on Hand"), max_digits=12, decimal_places=2
    )
    minimum_stock_level = models.PositiveIntegerField(
        _("Minimum Stock Level"),
        default=0,
        help_text=_("The threshold that triggers a 'Low Stock' alert for procurement."),
    )
    storage_temperature = models.DecimalField(
        _("Target Storage Temp (°C)"),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_(
            "Specific temperature requirement for this stock (e.g., -18.00 for frozen)."
        ),
    )
    unit_of_measure = models.CharField(_("UOM"), max_length=20, choices=UOM_CHOICES)
    readiness_status = models.CharField(
        _("Readiness"), max_length=20, choices=READINESS_CHOICES, default="READY"
    )
    batch_number = models.CharField(
        _("Batch Number"), max_length=100, unique=True, db_index=True
    )

    # Blueprint for stock_metadata:
    # {
    #   "production_date": "2026-02-18",
    #   "best_before": "2026-03-18",
    #   "bin_location": "Cold Room 1",
    #   "valuation_at_production": 5000.00,
    #   "currency": "TZS"
    # }

    stock_metadata = models.JSONField(_("Stock Metadata"), default=dict)
    last_inspected = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "product_stock"
        unique_together = (
            "product_type",
            "storage_unit",
            "readiness_status",
            "batch_number",
        )
        indexes = [
            GinIndex(fields=["stock_metadata"], name="stock_meta_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Product Stock for '{self.product_type.name}' "
                f"from: {old_data} to: {self.quantity_on_hand}{self.unit_of_measure}, "
                f"batch {self.batch_number}, readiness {self.readiness_status}"
            )
        return (
            f"Created Product Stock for '{self.product_type.name}' "
            f"batch {self.batch_number}, quantity {self.quantity_on_hand}{self.unit_of_measure}, "
            f"readiness {self.readiness_status}, stored in {self.storage_unit}"
        )

    @property
    def days_to_expiry(self):
        """Calculates shelf life remaining."""
        if self.stock_metadata.get("expiry_date"):
            expiry = datetime.strptime(
                self.stock_metadata["expiry_date"], "%Y-%m-%d"
            ).date()
            return (expiry - timezone.now().date()).days
        return None

    @property
    def is_low_stock(self):
        """Quick check to see if restocking is required."""
        return self.quantity_on_hand <= self.minimum_stock_level

    def __str__(self):
        return f"{self.product_type.name} ({self.readiness_status}) - {self.quantity_on_hand}"


class StockMovement(models.Model):
    """Every single change in stock: Sales, Restocks, Decay, or Transfers."""

    stock = models.ForeignKey(
        ProductStock, on_delete=models.CASCADE, related_name="movements"
    )
    movement_type = models.CharField(max_length=20, choices=STOCK_MOVEMENT_TYPES)
    quantity_change = models.DecimalField(max_digits=12, decimal_places=2)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    timestamp = models.DateTimeField(default=timezone.now)
    reference_id = models.CharField(max_length=50, blank=True, null=True)
    is_reversible = models.BooleanField(
        _("Is Reversible"),
        default=True,
        help_text=_(
            "If True, this movement can be rolled back (e.g., for order cancellations)."
        ),
    )
    # {
    #   "reason_code": "SPOILAGE",
    #   "approved_by": "Manager_John",
    #   "incident_report_url": "s3://reports/2026/spoiled_eggs_01.pdf",
    #   "temperature_at_discovery": "28°C"
    # }
    movement_metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "stock_movement"
        indexes = [
            GinIndex(fields=["movement_metadata"], name="stock_move_meta_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Stock Movement for Product '{self.stock.product_type.name}' "
                f"from: {old_data} to: type {self.movement_type}, change {self.quantity_change}, "
                f"performed by {self.performed_by}"
            )
        return (
            f"Recorded Stock Movement for Product '{self.stock.product_type.name}' "
            f"type {self.movement_type}, change {self.quantity_change}, "
            f"performed by {self.performed_by}, reference {self.reference_id}"
        )

    @transaction.atomic
    def reverse_movement(self, user):
        """Handles cancellations by creating a compensating entry."""
        if not self.is_reversible:
            raise ValidationError(_("This movement type cannot be reversed."))

        StockMovement.objects.create(
            stock=self.stock,
            movement_type="ADJUSTMENT",
            quantity_change=-(self.quantity_change),
            performed_by=user,
            reference_id=f"REV-{self.id}",
            movement_metadata={"reason": f"Reversal of Movement {self.id}"},
        )

    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        When a movement is saved, update the ProductStock quantity.
        This ensures the 'Ledger' and 'Real-time balance' never drift apart.
        """
        is_new = self._state.adding
        if is_new:
            self.stock.quantity_on_hand += self.quantity_change
            if self.stock.quantity_on_hand < 0:
                raise ValidationError(_("Insufficient stock for this movement."))

            self.stock.save()
        super().save(*args, **kwargs)
