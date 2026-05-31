from django.db import models

from common.mixins import BaseEnterpriseAuditModelMixin


class CropProduction(BaseEnterpriseAuditModelMixin):
    """
    Inarekodi mazao yanayolimwa ili kulisha kuku au biashara,
    ikitumia mbolea kutoka kwa kuku.
    """

    class ProductionStatus(models.TextChoices):
        PLANTED = "PLANTED", "planted"
        GROWING = "GROWING", "Inakua"
        HARVESTED = "HARVESTED", "Imevunwa"
        FAILED = "FAILED", "Imeharibika"

    block = models.ForeignKey("sfap.FarmBlock", on_delete=models.CASCADE)
    crop_name = models.CharField(max_length=100)  # Mfano: Alizeti, Mtama
    status = models.CharField(
        max_length=20,
        choices=ProductionStatus.choices,
        default=ProductionStatus.PLANTED,
    )

    # Ratiba
    planting_date = models.DateField()
    harvest_date = models.DateField(null=True, blank=True)

    # Mavuno (Yield)
    estimated_yield_kg = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0
    )
    actual_yield_kg = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    # Mzunguko wa Virutubisho kutoka kwa kuku
    manure_used_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    production_metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Uzalishaji wa Mazao"
        verbose_name_plural = "Uzalishaji wa Mazao"

    def __str__(self):
        return f"{self.crop_name} ({self.get_status_display()}) - {self.block.name}"


class EcologicalInput(BaseEnterpriseAuditModelMixin):
    """
    Inafuatilia pembejeo za asili (Organic Inputs)
    Kama vile: Wadudu (BSF), Nyasi, au Mbolea ya vimelea.
    """

    class UnitChoices(models.TextChoices):
        KG = "KG", "Kilogramu"
        LITER = "L", "Lita"
        PIECE = "PCS", "Idadi/Vipande"

    farm = models.ForeignKey("sfap.Farm", on_delete=models.CASCADE)
    input_name = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(
        max_length=10, choices=UnitChoices.choices, default=UnitChoices.KG
    )

    # Thamani ya Kifedha (Defaulting to TZS)
    estimated_cost = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.0, help_text="Gharama kwa TZS"
    )

    # Mabadiliko hapa: Inaweza kuwa null kama inatoka nje ya shamba (External Vendor)
    origin = models.ForeignKey(
        "sfap.FarmBlock",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Kitalu/Meli ilikotoka (Acha wazi kama inatoka nje ya shamba)",
    )

    class Meta:
        verbose_name = "Pembejeo ya Kiasili"
        verbose_name_plural = "Pembejeo za Kiasili"

    def __str__(self):
        return f"{self.input_name} - {self.quantity} {self.unit}"


from rest_framework import serializers


class LogHarvestSerializer(serializers.Serializer):
    actual_yield_kg = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0.01
    )
    unit_cost_tzs = serializers.DecimalField(
        max_digits=12, decimal_places=2, default=0.00, min_value=0.00
    )


from rest_framework import status, viewset
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import CropProduction
from .serializers import (  # Assuming you have a standard model serializer
    CropProductionSerializer,
    LogHarvestSerializer,
)
from .services import CropHarvestLogisticsService


class CropProductionViewSet(viewsets.ModelViewSet):
    """
    ViewSet ya kudhibiti mzunguko mzima wa uzalishaji wa mazao (Crop Production).
    """

    queryset = CropProduction.objects.all()
    serializer_class = CropProductionSerializer

    @action(detail=True, methods=["post"], url_path="log-harvest")
    def log_harvest(self, request, pk=None):
        """
        Endpoint ya kurekodi mavuno ya zao husika na kuhamishia ghalani kama chakula cha kuku.
        Mfano wa URL: /api/crop-productions/{id}/log-harvest/
        """
        # 1. Thibitisha data ya data ya kuingizwa kwa kutumia serializer yetu
        serializer = LogHarvestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Chopoa data iliyosafishwa (Validated Data)
        actual_yield = serializer.validated_data["actual_yield_kg"]
        unit_cost = serializer.validated_data["unit_cost_tzs"]

        # 3. Tekeleza mchakato wa kimantiki kupitia safu ya huduma (Service Layer)
        try:
            stock = CropHarvestLogisticsService.process_harvest_to_feed_stock(
                crop_production_id=pk,
                actual_yield=actual_yield,
                unit_cost_tzs=unit_cost,
            )
            return Response(
                {
                    "status": "success",
                    "message": "Mavuno yamefanikiwa kurekodiwa na stoki ya chakula imeongezwa.",
                    "ingredient": stock.ingredient_name,
                    "current_stock_kg": float(stock.available_qty_kg),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CropProductionViewSet

router = DefaultRouter()
router.register(r"crop-productions", CropProductionViewSet, basename="crop-production")

urlpatterns = [
    path("", include(router.urls)),
]


from decimal import Decimal

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError  # FIX: Aliyekosekana kwenye import
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from helpers.choices import CURRENCY_CHOICES
from utils.audit_track import FarmAuditBaseModel


class FeedType(FarmAuditBaseModel):
    """Defines the nutritional profile and pricing of feed."""

    name = models.CharField(_("Feed Name"), max_length=100, unique=True)
    brand = models.CharField(_("Brand/Manufacturer"), max_length=100, blank=True)

    # {
    #    "protein_pct": 22.0,
    #    "metabolizable_energy_kcal": 3000,
    #    "calcium_pct": 1.0,
    #    "lysine_pct": 1.2,
    #    "is_medicated": true
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


# Katika module ya kuku (e.g., poultry_feed/models.py au sfap/models.py)
class FeedIngredientStock(BaseEnterpriseAuditModelMixin):
    """
    Inafuatilia stoki ya malighafi za chakula cha kuku zilizopo ghalani.
    """

    ingredient_name = models.CharField(max_length=100)  # Mfano: Alizeti, Mtama
    available_qty_kg = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    unit_cost_per_kg = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.0
    )  # Kwa TZS
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.ingredient_name} - {self.available_qty_kg} KG"


class FeedInventory(FarmAuditBaseModel):
    """Tracks stock levels in silos or warehouses."""

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

    # [
    #    {
    #      "date": "2026-02-01",
    #      "qty_received": 500.0,
    #      "expiry_date": "2026-08-01",
    #      "supplier_invoice": "INV-9982",
    #      "batch_number": "BATCH-X-01"
    #    }
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
            # FIX: Salama zaidi kama old_data si dictionary tupu
            old_qty = (
                old_data.get("total_quantity_kg")
                if isinstance(old_data, dict)
                else old_data
            )
            return (
                f"Updated Feed Inventory for '{self.feed_type.name}' "
                f"from total: {old_qty}kg "
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

    batch = models.ForeignKey(
        "sfap.Batch",
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

    # FIX: Tumeongeza field ya Tarehe ya wazi ili kufanya unique_together ifanye kazi ipasavyo badala ya DateTime
    log_date = models.DateField(
        _("Log Date"),
        auto_now_add=True,
        help_text=_(
            "The specific day this consumption is recorded for optimization tracking."
        ),
    )

    # {
    #    "waste_kg": 2.5,
    #    "feeder_status": "Clean",
    #    "water_liters_added": 50,
    #    "abnormal_feeding_behavior": false
    # }
    consumption_notes = models.JSONField(
        _("Consumption Notes"),
        default=dict,
        blank=True,
        help_text=_("Stores waste data, feeder status, and behavioral observations."),
    )

    class Meta:
        db_table = "feed_consumption"
        # FIX: Sasa inalinda zisirekodiwe data mbili za aina moja ya chakula kwa batch moja kwa siku husika
        unique_together = ("batch", "log_date", "feed_type")
        ordering = ["-log_date"]
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
        """Calculates what the birds actually ate by parsing JSON data."""
        # FIX: Tunatoa waste kutoka kwa JSON moja kwa moja ili kuzuia split source of truth
        waste = self.consumption_notes.get("waste_kg", 0)
        try:
            return self.quantity_used_kg - Decimal(str(waste))
        except Exception:
            return self.quantity_used_kg

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
            try:
                inventory = FeedInventory.objects.select_for_update().get(
                    feed_type=self.feed_type
                )
            except FeedInventory.DoesNotExist:
                raise ValidationError(
                    _(
                        f"Hakuna stoki iliyosajiliwa kwa ajili ya aina hii ya chakula: {self.feed_type.name}."
                    )
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


from decimal import Decimal

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from helpers.choices import CURRENCY_CHOICES
from utils.audit_track import FarmAuditBaseModel


class FeedType(FarmAuditBaseModel):
    """Defines the nutritional profile and pricing of feed."""

    class SourceChoices(models.TextChoices):
        COMMERCIAL = "COMMERCIAL", _("Kibiashara / Kununuliwa")
        FARM_PRODUCED = "FARM_PRODUCED", _("Kiasili / Limeshindwa Shambani")

    name = models.CharField(_("Feed Name"), max_length=100, unique=True)
    brand = models.CharField(
        _("Brand/Manufacturer"),
        max_length=100,
        blank=True,
        help_text=_("Acha wazi kama limetengenezwa shambani."),
    )
    feed_source = models.CharField(
        _("Feed Source"),
        max_length=20,
        choices=SourceChoices.choices,
        default=SourceChoices.COMMERCIAL,
    )

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

    def __str__(self):
        return f"{self.name} ({self.get_feed_source_display()})"


class FeedInventory(FarmAuditBaseModel):
    """Tracks stock levels in silos or warehouses."""

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
    )
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

    def __str__(self):
        return f"{self.feed_type.name} - {self.total_quantity_kg}kg"


class FeedConsumption(FarmAuditBaseModel):
    """
    Tracks how much a batch is eating and drinking daily.
    Critical for calculating Feed Conversion Ratio (FCR).
    """

    batch = models.ForeignKey(
        "sfap.Batch",
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
    waste_amount_kg = models.DecimalField(
        _("Waste Amount (KG)"), max_digits=10, decimal_places=2, default=0.00
    )

    # UPGRADE: Imetolewa kwenye JSON kusaidia dashboard KPI telemetry ya haraka kuzuia magonjwa
    water_liters_added = models.DecimalField(
        _("Water Intake (Liters)"), max_digits=10, decimal_places=2, default=0.00
    )

    log_date = models.DateField(_("Log Date"), auto_now_add=True)
    consumption_notes = models.JSONField(
        _("Consumption Notes"), default=dict, blank=True
    )

    class Meta:
        db_table = "feed_consumption"
        unique_together = ("batch", "log_date", "feed_type")
        ordering = ["-log_date"]
        verbose_name = _("Feed Consumption Log")

        permissions = [
            ("update_water_intake", "Can update water intake"),
            ("view_kpi_dashboard", "Can view KPI dashboard"),
        ]

    @property
    def actual_intake(self):
        """Calculates what the birds actually ate safely."""
        return max(Decimal("0.00"), self.quantity_used_kg - self.waste_amount_kg)

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Saves logs and dynamically adjusts physical warehouse inventory."""

        # 1. Kokotoa mabadiliko ya stoki (Calculate change delta)
        if self._state.adding:
            # Rekodi mpya: chukua kiasi chote kilichowekwa
            quantity_delta = self.quantity_used_kg
        else:
            # Rekodi ya zamani inayofanyiwa mabadiliko (Update)
            old_instance = FeedConsumption.objects.get(pk=self.pk)
            quantity_delta = self.quantity_used_kg - old_instance.quantity_used_kg

        if quantity_delta != 0:
            try:
                inventory = FeedInventory.objects.select_for_update().get(
                    feed_type=self.feed_type
                )
            except FeedInventory.DoesNotExist:
                raise ValidationError(
                    _(
                        f"Hakuna stoki iliyosajiliwa kwa ajili ya: {self.feed_type.name}."
                    )
                )

            # Angalia kama kuna upungufu ghalani kabla ya kuruhusu makabadiliko
            if inventory.total_quantity_kg < quantity_delta:
                raise ValidationError(
                    _(
                        f"Inventory Shortage: Ghala lina kilo {inventory.total_quantity_kg} tu za {self.feed_type.name}."
                    )
                )

            # Punguza au rudisha mali ghalani kulingana na delta value
            inventory.total_quantity_kg -= quantity_delta
            inventory.save()

        super().save(*args, **kwargs)

    @transaction.atomic
    def delete(self, *args, **kwargs):
        """Rudisha chakula ghalani kama logi ikifutwa na msimamizi."""
        inventory = FeedInventory.objects.select_for_update().get(
            feed_type=self.feed_type
        )
        inventory.total_quantity_kg += self.quantity_used_kg
        inventory.save()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.batch.batch_id}: {self.quantity_used_kg}kg"


from datetime import datetime  # FIX: Aliyekosekana kuzuia NameError crash

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import (
    ValidationError,
)  # FIX: Hakikisha ipo kwa ajili ya validation
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ..helpers import (
    CURRENCY_CHOICES,
    PRODUCT_CATEGORY_CHOICES,
    READINESS_CHOICES,
    STOCK_MOVEMENT_TYPES,
    STORAGE_UNIT_TYPES,
    UOM_CHOICES,
)
from ..utils import FarmAuditBaseModel


class Product(FarmAuditBaseModel):
    """Defines the global catalog (e.g., Broiler Meat, Organic Eggs)."""

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
            return f"Updated Product '{self.name}' from: {old_data} to: category {self.category}, specs {self.specs}"
        return f"Created Product '{self.name}' in category {self.get_category_display()}, specs {self.specs}"

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class PackagedProduct(BaseEnterpriseAuditModelMixin):
    """
    Specific items ready for retail (e.g., '1kg Frozen Wings').
    Enables 'Farm-to-Fork' traceability.
    """

    session = models.ForeignKey(
        ProcessingSession, on_delete=models.CASCADE, related_name="packages"
    )

    product_stock_ref = models.ForeignKey(
        settings.STOCK_PRODUCT_REFERENCE,
        on_delete=models.CASCADE,
        verbose_name=_("Inventory Catalog Reference"),
    )
    production_line = models.CharField(
        _("Production Line"), max_length=50, db_index=True, blank=True
    )

    label_code = models.CharField(
        _("QR/Barcode"), max_length=100, unique=True, db_index=True
    )
    weight = models.DecimalField(_("Unit Weight (KG)"), max_digits=10, decimal_places=2)

    # Blueprint for packaging_metadata:
    # {
    #   "material_type": "Vacuum Plastic",
    #   "seal_integrity_check": "Pass",
    #   "storage_temp_celsius": -18,
    #   "production_line": "LINE_02"
    # }
    packaging_metadata = models.JSONField(
        _("Packaging Specs"),
        default=dict,
        help_text=_("Stores material types, seal checks, and storage conditions."),
    )

    expiry_date = models.DateField(_("Expiry Date"))

    class Meta:
        db_table = "packaged_product"
        verbose_name = _("Packaged Product")
        indexes = [
            GinIndex(fields=["packaging_metadata"], name="package_meta_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Packaged Product '{self.label_code}' "
                f"from: {old_data} to: weight {self.weight}kg, "
                f"expiry {self.expiry_date}"
            )
        return (
            f"Packaged Product '{self.label_code}' created from Session '{self.session.id}' "
            f"— {self.weight}kg, expiry {self.expiry_date}, "
            f"line {self.production_line}, stock ref {self.product_stock_ref.product_name}"
        )

    def clean(self):
        """Ensures we don't 'create' weight out of thin air."""
        existing_pkg_weight = PackagedProduct.objects.filter(
            session=self.session
        ).exclude(pk=self.pk).aggregate(total=models.Sum("weight"))["total"] or Decimal(
            "0.00"
        )

        if (existing_pkg_weight + self.weight) > self.session.total_dressed_weight:
            raise ValidationError(
                _(
                    f"Traceability Error: Total packaged weight exceeds the "
                    f"available dressed weight ({self.session.total_dressed_weight}kg) for this session."
                )
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.label_code} - {self.product_stock_ref.product_name}"


class WarehouseLocation(FarmAuditBaseModel):
    """Physical facilities (e.g., Dodoma Main, Mwanza Staging)."""

    name = models.CharField(_("Location Name"), max_length=100, unique=True)
    code = models.CharField(_("Warehouse Code"), max_length=20, unique=True)
    address = models.CharField(_("Warehouse Address"), max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "warehouse_location"
        verbose_name = _("Warehouse Location")
        verbose_name_plural = _("Warehouse Locations")

    def get_log_message(self, old_data=None):
        if old_data:
            return f"Updated Warehouse '{self.name}' from: {old_data} to: code {self.code}, address {self.address}"
        return f"Created Warehouse '{self.name}' (Code: {self.code}, Address: {self.address})"

    def __str__(self):
        return f"{self.name} ({self.code})"


class Zone(FarmAuditBaseModel):
    """Sections like 'Cold Storage', 'Electronics', or 'Loading Dock'."""

    warehouse = models.ForeignKey(
        WarehouseLocation, on_delete=models.CASCADE, related_name="zones"
    )
    name = models.CharField(_("Zone Name"), max_length=100)
    code = models.CharField(_("Zone Code"), max_length=10, blank=True)

    class Meta:
        db_table = "warehouse_zone"
        verbose_name = _("Warehouse Zone")
        verbose_name_plural = _("Warehouse Zones")

    def get_log_message(self, old_data=None):
        if old_data:
            return f"Updated Zone '{self.name}' in Warehouse '{self.warehouse.name}' from: {old_data} to: code {self.code}"
        return f"Created Zone '{self.name}' in Warehouse '{self.warehouse.name}' (Code: {self.code})"

    def __str__(self):
        return f"{self.warehouse.code} - {self.name}"


class StorageUnit(FarmAuditBaseModel):
    """The specific mean: Shelf A1, Freezer 2, or Drawer 10."""

    zone = models.ForeignKey(
        Zone, on_delete=models.CASCADE, related_name="storage_units"
    )
    unit_code = models.CharField(_("Unit Code"), max_length=20)
    unit_type = models.CharField(
        _("Storage Mean"), max_length=20, choices=STORAGE_UNIT_TYPES, default="SHELF"
    )
    max_capacity = models.IntegerField(_("Max Capacity"), default=0)

    class Meta:
        db_table = "storage_unit"
        verbose_name = _("Storage Unit")
        verbose_name_plural = _("Storage Units")
        unique_together = ("zone", "unit_code")

    def get_log_message(self, old_data=None):
        if old_data:
            return f"Updated Storage Unit '{self.unit_code}' in Zone '{self.zone.name}' from: {old_data} to: type {self.unit_type}, capacity {self.max_capacity}"
        return f"Created Storage Unit '{self.unit_code}' in Zone '{self.zone.name}' type {self.unit_type}, capacity {self.max_capacity}"

    def __str__(self):
        return f"{self.get_unit_type_display()} {self.unit_code}"


class ProductStock(FarmAuditBaseModel):
    """Real-time inventory linking Production (Batch) to Sale (Revenue)."""

    product_type = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="current_stock"
    )
    storage_unit = models.ForeignKey(
        StorageUnit, on_delete=models.PROTECT, related_name="stock_items"
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
    unit_of_measure = models.CharField(_("UOM"), max_length=20, choices=UOM_CHOICES)
    readiness_status = models.CharField(
        _("Readiness"), max_length=20, choices=READINESS_CHOICES, default="READY"
    )
    batch_number = models.CharField(
        _("Batch Number"), max_length=100, unique=True, db_index=True
    )
    stock_metadata = models.JSONField(_("Stock Metadata"), default=dict, blank=True)
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
            return f"Updated Stock for '{self.product_type.name}' from: {old_data} to: {self.quantity_on_hand}{self.unit_of_measure}"
        return f"Created Stock for '{self.product_type.name}' batch {self.batch_number}, quantity {self.quantity_on_hand}"

    @property
    def days_to_expiry(self):
        """Calculates shelf life remaining safely."""
        # FIX: Tumeondoa uwezekano wa kucrash kwa sababu datetime sasa imekuwa imported juu
        expiry_str = self.stock_metadata.get("expiry_date")
        if expiry_str:
            try:
                expiry = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                return (expiry - timezone.now().date()).days
            except (ValueError, TypeError):
                return None
        return None

    @property
    def is_low_stock(self):
        return self.quantity_on_hand <= self.minimum_stock_level

    def __str__(self):
        return (
            f"{self.product_type.name} - {self.quantity_on_hand} {self.unit_of_measure}"
        )


class StockMovement(
    FarmAuditBaseModel
):  # UPGRADE: Imerudishwa kwenye FarmAuditBaseModel kulinda mfumo wako wa audit logs
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
    is_reversible = models.BooleanField(_("Is Reversible"), default=True)
    movement_metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "stock_movement"
        indexes = [
            GinIndex(fields=["movement_metadata"], name="stock_move_meta_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        return f"Movement {self.movement_type} affecting {self.stock.product_type.name} by {self.quantity_change}"

    @transaction.atomic
    def reverse_movement(self, user):
        """Handles cancellations by creating a compensating entry safely."""
        if not self.is_reversible:
            raise ValidationError(
                _("Movement hii tayari ishabadilishwa au haina uwezo wa kugeuzwa tena.")
            )

        # FIX: Zima uwezo wa kureverse tena kwenye instance hii kuzuia double reversals bugs
        self.is_reversible = False
        self.save(update_fields=["is_reversible"])

        # Hii itatengeneza log mpya ambayo nayo itajipunguza/itajiendesha kwenye save() hapa chini
        return StockMovement.objects.create(
            stock=self.stock,
            movement_type="ADJUSTMENT",
            quantity_change=-(self.quantity_change),
            performed_by=user,
            reference_id=f"REV-{self.id}",
            is_reversible=False,
            movement_metadata={"reason": f"Reversal of Movement {self.id}"},
        )

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Updates ProductStock quantities safely using pessimistic concurrency database locks."""
        is_new = self._state.adding
        if is_new:
            # FIX: Pata na ufunge (Lock) ProductStock row kwenye database kuzuia kabisa Race Condition za watumiaji wengi
            locked_stock = ProductStock.objects.select_for_update().get(
                pk=self.stock_id
            )

            # Fanya hesabu kwenye record iliyofungwa (Safe Database State)
            locked_stock.quantity_on_hand += self.quantity_change

            if locked_stock.quantity_on_hand < 0:
                raise ValidationError(
                    _("Mavuno/Bidhaa hazitoshi kwenye stoki kukamilisha mchakato huu.")
                )

            locked_stock.save()

            # Weka kiwango kipya kwenye instance ya sasa ili iandikwe kwa usahihi
            self.stock = locked_stock

        super().save(*args, **kwargs)


from django.db import models
from django.utils.translation import gettext_lazy as _


class StorageUnitType(models.TextChoices):
    SHELF = "SHELF", _("Shelf (Rafu)")
    KABATI = "KABATI", _("Cabinet (Kabati)")
    CLIPBOARD = "CLIPBOARD", _("Clipboard")
    DRAWER = "DRAWER", _("Drawer (Droo)")
    COLD_ROOM = "COLD_ROOM", _("Cold Room Rack")


class ProductionStatus(models.TextChoices):
    PLANTED = "PLANTED", _("Imepandwa")
    GROWING = "GROWING", _("Inakua")
    HARVESTED = "HARVESTED", _("Imevunwa")
    FAILED = "FAILED", _("Imeharibika")
