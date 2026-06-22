import datetime
from decimal import Decimal

from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Count, Sum
from django.utils.translation import gettext_lazy as _

from common.constants import current_time, now
from common.mixins import BaseEnterpriseAuditModelMixin

# Create your models here.


class ProductStock(BaseEnterpriseAuditModelMixin):
    """
    Real-time inventory linking Production (Batch) to Sale (Revenue).
    Tracks readiness (Ready vs WIP) and physical storage (Kabati/Shelf).
    """

    product_type = models.ForeignKey(
        "ipss.ProductVariant", on_delete=models.PROTECT, related_name="current_stock"
    )
    storage_unit = models.ForeignKey(
        "ipss.StorageUnit", on_delete=models.PROTECT, related_name="stock_items"
    )
    quantity_on_hand = models.DecimalField(
        _("Quantity on Hand"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.00)],
    )
    minimum_stock_level = models.PositiveIntegerField(
        _("Minimum Stock Level"), default=0
    )
    storage_temperature = models.DecimalField(
        _("Target Storage Temp (°C)"),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    unit_of_measure = models.ForeignKey(
        "config.UnitOfMeasure", on_delete=models.RESTRICT
    )
    readiness_status = models.ForeignKey(
        "config.StockReadinessStatus", on_delete=models.RESTRICT
    )
    batch_number = models.CharField(
        _("Batch Number"), max_length=100, unique=True, db_index=True
    )
    stock_metadata = models.JSONField(_("Stock Metadata"), default=dict, blank=True)
    last_inspected = models.DateTimeField(default=now)

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

    @property
    def days_to_expiry(self) -> int | None:
        """Calculates shelf life remaining."""
        if self.stock_metadata.get("expiry_date"):
            expiry = datetime.strptime(
                self.stock_metadata["expiry_date"], "%Y-%m-%d"
            ).date()
            return (expiry - current_time.date()).days
        return None

    @property
    def is_low_stock(self) -> bool:
        """Quick check to see if restocking is required."""
        return self.quantity_on_hand <= self.minimum_stock_level

    @property
    def total_packaged_units_count(self) -> int:
        """Inarudisha idadi kamili ya pakiti halisi zilizopo ghalani Sasa Hivi."""
        from ipss.models import PackagedProduct

        result = PackagedProduct.objects.filter(
            variant_ref=self.product_type,
            session__source_batch__batch_id=self.batch_number,
            status="IN_STOCK",
        ).aggregate(total_packets=Count("id"))

        return result["total_packets"] or 0

    @property
    def total_packaged_weight(self) -> Decimal:
        """Inapiga hesabu ya uzito wa pakiti zilizopo ghalani Sasa Hivi."""
        from ipss.models import PackagedProduct

        result = PackagedProduct.objects.filter(
            variant_ref=self.product_type,
            session__source_batch__batch_id=self.batch_number,
            status="IN_STOCK",
        ).aggregate(total_weight=Sum("weight"))

        return result["total_weight"] or Decimal("0.00")

    def __str__(self):
        return f"{self.product_type.name} ({self.product_type.get_cut_type_display()}) - {self.quantity_on_hand}"

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


class StockMovement(BaseEnterpriseAuditModelMixin):
    """Tracks Every single change in stock: Sales, Restocks, Decay, or Transfers."""

    stock = models.ForeignKey(
        ProductStock, on_delete=models.CASCADE, related_name="movements"
    )
    status = models.ForeignKey("config.StockMovementType", on_delete=models.RESTRICT)
    quantity_change = models.DecimalField(max_digits=12, decimal_places=2)
    units_change = models.IntegerField(
        default=0,
        help_text=_("Idadi ya pakiti zilizopungua au kuongezeka (mf. -1, +10)"),
    )
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
        is_new = self._state.adding
        if is_new:
            locked_stock = ProductStock.objects.select_for_update().get(
                pk=self.stock_id
            )
            locked_stock.quantity_on_hand += self.quantity_change
            if locked_stock.quantity_on_hand < 0:
                raise ValidationError(
                    _("Mavuno/Bidhaa hazitoshi ghalani kukamilisha mchakato huu.")
                )
            locked_stock.save()
            self.stock = locked_stock
        super().save(*args, **kwargs)

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
