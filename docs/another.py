from datetime import datetime
from decimal import Decimal
from django.db import models, transaction
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Tukichukulia kuwa hizi zimeshaandikwa kwenye helpers.py kama tulivyozirekebisha
from ..helpers import (
    ProductCategory,
    StorageUnitType,
    StockReadinessStatus,
    StockMovementType,
    UnitOfMeasure
)
from ..utils import FarmAuditBaseModel


# --- PLACEHOLDER KWA AJILI YA USINDIKAJI ---
class ProcessingSession(BaseEnterpriseAuditModelMixin):
    """
    Tracks a specific slaughter/packaging run.
    Acts as the 'Converter' from Live Birds to Meat Inventory.
    """

    plant = models.ForeignKey(
        ProcessingPlant, on_delete=models.PROTECT, related_name="sessions"
    )

    source_batch = models.ForeignKey(
        'sfap.Batch',
        on_delete=models.PROTECT,
        related_name="processing_runs",
        verbose_name=_("Source Batch"),
    )
    assigned_workers = models.ManyToManyField(
        'hrms.Employee',
        related_name="session_workers",
        blank=True,
        verbose_name=_("Assigned Staff"),
    )

    birds_processed = models.PositiveIntegerField(_("Birds Processed"))
    live_birds_count = models.PositiveIntegerField(_("Live Birds Input"))
    total_live_weight = models.DecimalField(
        _("Live Weight (KG)"), max_digits=12, decimal_places=2
    )
    total_dressed_weight = models.DecimalField(
        _("Dressed Weight (KG)"), max_digits=12, decimal_places=2
    )

    # Blueprint for slaughter_data:
    # {
    #   "grade_a": 400, "grade_b": 50, "rejects": 5,
    #   "water_usage_liters": 1200,
    #   "cost_per_bird_slaughter": 200.00
    # }
    slaughter_data = models.JSONField(_("Slaughter Metrics"), default=dict)

    # Blueprint for environmental_logs:
    # {
    #   "scald_water_temp": 60.5,
    #   "stun_voltage": 110,
    #   "scald_time_sec": 120,
    #   "chiller_temp": 4.0,
    #   "defects_count": 5
    # }
    environmental_logs = models.JSONField(
        _("Processing Parameters"),
        default=dict,
        blank=True,
        help_text=_("Audit trail for water temperature, voltage, and safety metrics."),
    )

    start_time = models.DateTimeField(_("Session Start"))
    end_time = models.DateTimeField(_("Session End"))

    yield_percentage = models.DecimalField(
        _("Yield Percentage (%)"), max_digits=5, decimal_places=2, editable=False
    )
    temperature_recorder = models.CharField(_("Temperature Recorded"), max_length=100)
    rejected_birds = models.PositiveIntegerField(
        _("Rejects/Condemned"),
        default=0,
        help_text=_("Birds rejected during inspection for health/quality reasons."),
    )

    class Meta:
        db_table = "processing_session"
        verbose_name = _("Processing Session")
        ordering = ["-start_time"]
        indexes = [
            GinIndex(fields=["environmental_logs"], name="environmental_logs_gin_idx"),
        ]

    def clean(self):
        """Cross-checks bird counts and worker safety."""
        total_accounted = self.birds_processed + self.rejected_birds
        if total_accounted > self.live_birds_count:
            raise ValidationError(
                _(
                    f"Count Mismatch: You accounted for {total_accounted} birds, "
                    f"but only {self.live_birds_count} were received from the farm."
                )
            )

        if self.total_dressed_weight >= self.total_live_weight:
            raise ValidationError(
                _("Dressed weight cannot be greater than or equal to Live weight.")
            )

    def add_worker_to_session(self, worker):
        """Checks health clearance before adding worker to the M2M field."""
        if (
            not hasattr(worker, "employee_profile")
            or not worker.employee_profile.is_health_compliant
        ):
            raise ValidationError(_("Worker health clearance expired or missing."))
        self.assigned_workers.add(worker)

    def save(self, *args, **kwargs):
        # Calculate Yield (Dressed vs Live Weight)
        if self.total_live_weight and self.total_live_weight > 0:
            self.yield_percentage = (
                self.total_dressed_weight / self.total_live_weight
            ) * 100
        else:
            self.yield_percentage = 0

        # Ensure clean() is called even if not using a ModelForm
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def bird_loss_count(self) -> int:
        """Difference between birds received and birds successfully dressed."""
        return self.live_birds_count - self.birds_processed

    @property
    def slaughter_shrinkage_kg(self) -> float:
        """Calculates physical weight lost during processing (blood, feathers, etc)."""
        return self.total_live_weight - self.total_dressed_weight

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Processing Session at Plant '{self.plant.name}' "
                f"for Batch '{self.source_batch.batch_id}' "
                f"from: {old_data} to: birds processed {self.birds_processed}, "
                f"yield {self.yield_percentage:.2f}%"
            )
        return (
            f"Processing Session started at Plant '{self.plant.name}' "
            f"for Batch '{self.source_batch.batch_id}' — "
            f"{self.birds_processed} birds processed, dressed weight {self.total_dressed_weight}kg, "
            f"yield {self.yield_percentage:.2f}%"
        )


# --- 1. MBINU YA KUTOFAUTISHA UKATAJI KWENYE KATALOGI ---
class MeatCutType(models.TextChoices):
    SLICE = "SLICE", _("Slice / Steak (Vipande vilivyokatwa nyembamba)")
    PART = "PART", _("Primal Cut / Part (Sehemu maalum kama Paja/Kidari)")
    PIECE = "PIECE", _("Countable Piece (Idadi kama Soseji/Mshikaki)")
    WHOLE = "WHOLE", _("Whole Carcass / Bird (Mzoga Mzima)")


class Product(FarmAuditBaseModel):
    """ Defines the global catalog (e.g., Broiler Meat, Organic Eggs). """
    name = models.CharField(_("Product Name"), max_length=100, unique=True)
    category = models.CharField(_("Category"), max_length=50, choices=ProductCategory.choices)
    specs = models.JSONField(_("Product Specifications"), default=dict, blank=True)

    class Meta:
        db_table = "product"
        verbose_name = _("Product Type")
        verbose_name_plural = _("Product Types")
        indexes = [
            GinIndex(fields=["specs"], name="product_specs_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return f"Updated Product '{self.name}' from: {old_data} to: category {self.category}, cut {self.cut_type}"
        return f"Created Product '{self.name}' in category {self.get_category_display()} ({self.get_cut_type_display()})"

    def __str__(self):
        return f"{self.name} ({self.get_cut_type_display()})"


class ProductVariant(FarmAuditBaseModel):
    """
    The Variant level enabling Amazon/AliExpress style selection.
    Combines the parent Product with specific physical attributes, pricing, and SKU.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants", verbose_name=_("Parent Product"))

    cut_type = models.CharField(_("Cut Type"), max_length=20, choices=MeatCutType.choices, default=MeatCutType.WHOLE)
    storage_state = models.CharField(_("Storage State"), max_length=20, choices=StorageState.choices, default=StorageState.FRESH)
    fat_level = models.CharField(_("Fat Content"), max_length=20, choices=FatLevel.choices, default=FatLevel.MEDIUM)

    sku = models.CharField(_("SKU / Item Code"), max_length=100, unique=True, db_index=True)

    # Enterprise Pricing Model
    if MoneyField:
        price = MoneyField(_("Unit Price"), max_digits=12, decimal_places=2, default_currency="TZS")
    else:
        price = models.DecimalField(_("Unit Price (TZS)"), max_digits=12, decimal_places=2)

    is_active = models.BooleanField(_("Is Available for Sale"), default=True)
    variant_metadata = models.JSONField(_("Variant Metadata"), default=dict, blank=True)

    class Meta:
        db_table = "product_variant"
        verbose_name = _("Product Variant")
        verbose_name_plural = _("Product Variants")
        unique_together = ("product", "cut_type", "storage_state", "fat_level")

    def __str__(self):
        return f"{self.product.name} - {self.get_cut_type_display()} [{self.get_storage_state_display()}]"


class PackagedProduct(FarmAuditBaseModel):
    """ Specific items ready for retail tagged to their architectural variants. """
    session = models.ForeignKey(
        ProcessingSession, on_delete=models.CASCADE, related_name="packages"
    )
    # FIX: Sasa inatwanga kwenye Variant badala ya Product kuu ya juu ya jumla
    variant_ref = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        verbose_name=_("Product Variant Reference"),
        related_name="packages"
    )
    production_line = models.CharField(_("Production Line"), max_length=50, db_index=True, blank=True)
    label_code = models.CharField(_("QR/Barcode"), max_length=100, unique=True, db_index=True)
    weight = models.DecimalField(_("Unit Weight (KG)"), max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    units_inside_package = models.PositiveIntegerField(_("Pieces Inside Package"), default=1)

    packaging_metadata = models.JSONField(
        _("Packaging Specs"),
        default=dict,
        blank=True,
        help_text=_("Stores material types, seal checks, and storage conditions."),
    )
    expiry_date = models.DateField(_("Expiry Date"))

    class Meta:
        db_table = "packaged_product"
        verbose_name = _("Packaged Product")
        verbose_name_plural = _("Packaged Products")
        indexes = [
            GinIndex(fields=["packaging_metadata"], name="package_meta_gin_idx"),
        ]

    def clean(self):
        """ Ensures packaged weight doesn't exceed the processing session yield capacity. """
        try:
            locked_session = ProcessingSession.objects.select_for_update().get(pk=self.session_id)
        except ProcessingSession.DoesNotExist:
            raise ValidationError(_("Processing Session inayorejelewa haipo."))

        existing_pkg_weight = PackagedProduct.objects.filter(
            session=locked_session
        ).exclude(pk=self.pk).aggregate(total=models.Sum("weight"))["total"] or Decimal("0.00")

        if (existing_pkg_weight + self.weight) > locked_session.total_dressed_weight:
            raise ValidationError(
                _(
                    f"Traceability Error: Uzito wa pakiti unazidi uzito wa "
                    f"mzoga uliopo kwenye session hii ({locked_session.total_dressed_weight}kg)."
                )
            )

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.label_code} - {self.variant_ref}"


# --- 2. USIMAMIZI WA MAENEO YA HILIFADHI (WAREHOUSE) ---
class WarehouseLocation(FarmAuditBaseModel):
    name = models.CharField(_("Location Name"), max_length=100, unique=True)
    code = models.CharField(_("Warehouse Code"), max_length=20, unique=True)
    address = models.CharField(_("Warehouse Address"), max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "warehouse_location"

    def __str__(self):
        return f"{self.name} ({self.code})"


class Zone(FarmAuditBaseModel):
    warehouse = models.ForeignKey(WarehouseLocation, on_delete=models.CASCADE, related_name="zones")
    name = models.CharField(_("Zone Name"), max_length=100)
    code = models.CharField(_("Zone Code"), max_length=10, blank=True)

    class Meta:
        db_table = "warehouse_zone"

    def __str__(self):
        return f"{self.warehouse.code} - {self.name}"


class StorageUnit(FarmAuditBaseModel):
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name="storage_units")
    unit_code = models.CharField(_("Unit Code"), max_length=20)
    unit_type = models.CharField(_("Storage Mean"), max_length=20, choices=StorageUnitType.choices, default=StorageUnitType.SHELF)
    max_capacity = models.IntegerField(_("Max Capacity"), default=0)

    class Meta:
        db_table = "storage_unit"
        unique_together = ("zone", "unit_code")

    def __str__(self):
        return f"{self.get_unit_type_display()} {self.unit_code}"


# --- 3. REALS-TIME STOCK BALANCE NA LEDGER ---
class ProductStock(FarmAuditBaseModel):
    product_type = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="current_stock")
    storage_unit = models.ForeignKey(StorageUnit, on_delete=models.PROTECT, related_name="stock_items")
    quantity_on_hand = models.DecimalField(_("Quantity on Hand"), max_digits=12, decimal_places=2, validators=[MinValueValidator(0.00)])
    minimum_stock_level = models.PositiveIntegerField(_("Minimum Stock Level"), default=0)
    storage_temperature = models.DecimalField(_("Target Storage Temp (°C)"), max_digits=5, decimal_places=2, null=True, blank=True)
    unit_of_measure = models.CharField(_("UOM"), max_length=20, choices=UnitOfMeasure.choices)
    readiness_status = models.CharField(_("Readiness"), max_length=20, choices=StockReadinessStatus.choices, default=StockReadinessStatus.READY)
    batch_number = models.CharField(_("Batch Number"), max_length=100, unique=True, db_index=True)
    stock_metadata = models.JSONField(_("Stock Metadata"), default=dict, blank=True)
    last_inspected = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "product_stock"
        unique_together = ("product_type", "storage_unit", "readiness_status", "batch_number")
        indexes = [
            GinIndex(fields=["stock_metadata"], name="stock_meta_gin_idx"),
        ]

    def __str__(self):
        return f"{self.product_type.name} ({self.product_type.get_cut_type_display()}) - {self.quantity_on_hand}"


class StockMovement(FarmAuditBaseModel):
    stock = models.ForeignKey(ProductStock, on_delete=models.CASCADE, related_name="movements")
    movement_type = models.CharField(max_digits=20, choices=StockMovementType.choices)
    quantity_change = models.DecimalField(max_digits=12, decimal_places=2)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    reference_id = models.CharField(max_length=50, blank=True, null=True)
    is_reversible = models.BooleanField(_("Is Reversible"), default=True)
    movement_metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "stock_movement"
        indexes = [
            GinIndex(fields=["movement_metadata"], name="stock_move_meta_gin_idx"),
        ]

    @transaction.atomic
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if is_new:
            locked_stock = ProductStock.objects.select_for_update().get(pk=self.stock_id)
            locked_stock.quantity_on_hand += self.quantity_change
            if locked_stock.quantity_on_hand < 0:
                raise ValidationError(_("Mavuno/Bidhaa hazitoshi ghalani kukamilisha mchakato huu."))
            locked_stock.save()
            self.stock = locked_stock
        super().save(*args, **kwargs)
