from django.db import models, transaction
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from helpers.choices import CURRENCY_CHOICES
from utils.audit_track import FarmAuditBaseModel


# Create your models here.


class FeedType(FarmAuditBaseModel):
    """ Defines the nutritional profile and pricing of feed."""

    name = models.CharField(_("Feed Name"), max_length=100, unique=True)
    brand = models.CharField(_("Brand/Manufacturer"), max_length=100, blank=True)

    # Blueprint for composition (Nutritional specs):
    # {
    #   "protein_pct": 22.0,
    #   "metabolizable_energy_kcal": 3000,
    #   "calcium_pct": 1.0,
    #   "lysine_pct": 1.2,
    #   "is_medicated": true
    # }
    composition = models.JSONField(
        _("Nutritional Composition"),
        default=dict,
        blank=True,
        help_text=_("Stores vitamins, proteins, and mineral percentages."),
    )
    unit_price = MoneyField(
        _("Unit Price (per KG)"),
        max_digits=14,
        decimal_places=2,
        default_currency="TZS",
    )

    class Meta:
        db_table = "feed_type"
        verbose_name = _("Feed Type")
        verbose_name_plural = _("Feed Types")
        indexes = [
            GinIndex(fields=["composition"], name="feed_composition_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Feed Type '{self.name}' "
                f"from: {old_data} to: "
                f"{{'brand': '{self.brand}', 'composition': {self.composition}, 'unit_price': '{self.unit_price}'}}"
            )
        return (
            f"Registered new Feed Type '{self.name}' "
            f"(Brand: {self.brand}, Price per KG: {self.unit_price})"
        )

    def __str__(self):
        return f"{self.name} ({self.brand})"


class FeedInventory(FarmAuditBaseModel):
    """ Tracks stock levels in silos or warehouses. """

    feed_type = models.OneToOneField(
        FeedType,
        on_delete=models.CASCADE,
        related_name="inventory",
        verbose_name=_("Feed Type"),
    )
    total_quantity_kg = models.DecimalField(
        _("Total Stock (KG)"), max_digits=12, decimal_places=2, default=0
    )
    reorder_level = models.DecimalField(
        _("Reorder Level (KG)"),
        max_digits=10,
        decimal_places=2,
        default=100,
        help_text=_("Triggers an alert when stock falls below this amount."),
    )

    # Blueprint for stock_logs (Arrival history):
    # [
    #   {
    #     "date": "2026-02-01",
    #     "qty_received": 500.0,
    #     "expiry_date": "2026-08-01",
    #     "supplier_invoice": "INV-9982",
    #     "batch_number": "BATCH-X-01"
    #   }
    # ]
    stock_logs = models.JSONField(
        _("Stock Logs"),
        default=list,
        help_text=_("Audit trail of feed arrivals and batch-specific metadata."),
    )

    class Meta:
        db_table = "feed_inventory"
        verbose_name = _("Feed Inventory")
        verbose_name_plural = _("Feed Inventories")
        indexes = [
            GinIndex(fields=["stock_logs"], name="feed_stock_log_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Feed Inventory for '{self.feed_type.name}' "
                f"from total: {old_data.get('total_quantity_kg')}kg "
                f"to: {self.total_quantity_kg}kg"
            )
        return (
            f"Created Feed Inventory for '{self.feed_type.name}' "
            f"with {self.total_quantity_kg}kg in stock (Reorder level: {self.reorder_level}kg)"
        )

    def __str__(self):
        return f"{self.feed_type.name} - {self.total_quantity_kg}kg"


class FeedConsumption(FarmAuditBaseModel):
    """
    Tracks how much a batch is eating.
    Critical for calculating Feed Conversion Ratio (FCR).
    """

    # Use string 'core.Batch' to prevent circular import
    batch = models.ForeignKey(
        'sfap.Batch',
        on_delete=models.CASCADE,
        related_name="feed_logs",
        verbose_name=_("Flock Batch"),
    )
    feed_type = models.ForeignKey(
        FeedType, on_delete=models.PROTECT, verbose_name=_("Feed Type")
    )
    quantity_used_kg = models.DecimalField(
        _("Quantity Used (KG)"), max_digits=10, decimal_places=2
    )

    # Blueprint for consumption_notes:
    # {
    #   "waste_kg": 2.5,
    #   "feeder_status": "Clean",
    #   "water_liters_added": 50,
    #   "abnormal_feeding_behavior": false
    # }
    consumption_notes = models.JSONField(
        _("Consumption Notes"),
        default=dict,
        blank=True,
        help_text=_("Stores waste data, feeder status, and behavioral observations."),
    )
    waste_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = "feed_consumption"
        unique_together = ("batch", "created_on", "feed_type")
        ordering = ["-created_on"]
        verbose_name = _("Feed Consumption Log")
        indexes = [
            GinIndex(fields=["consumption_notes"], name="feed_usage_notes_gin_idx"),
        ]

        permissions = [
            ("update_water_intake", "Can update water intake"),
            ("view_kpi_dashboard", "Can view KPI dashboard"),
        ]

    @property
    def actual_intake(self):
        """Calculates what the birds actually ate."""
        return self.quantity_used_kg - self.waste_amount

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Feed Consumption for Batch '{self.batch.batch_id}' "
                f"from: {old_data} to: {self.quantity_used_kg}kg of {self.feed_type.name}"
            )
        return (
            f"Recorded Feed Consumption for Batch '{self.batch.batch_id}' — "
            f"{self.quantity_used_kg}kg of {self.feed_type.name} used, "
            f"actual intake {self.actual_intake}kg, notes: {self.consumption_notes}"
        )

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Deduct used feed from the physical inventory silo."""
        is_new = self._state.adding
        if is_new:
            inventory = FeedInventory.objects.select_for_update().get(
                feed_type=self.feed_type
            )

            if inventory.total_quantity_kg < self.quantity_used_kg:
                raise ValidationError(
                    _(
                        f"Inventory Shortage: Only {inventory.total_quantity_kg}kg of "
                        f"{self.feed_type.name} left in stock."
                    )
                )

            # Deduct the stock
            inventory.total_quantity_kg -= self.quantity_used_kg
            inventory.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.batch.batch_id}: {self.quantity_used_kg}kg"
