from decimal import Decimal

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from common.choices import FatLevel, MeatCutType, ProductCategory, StorageState
from common.mixins import BaseEnterpriseAuditModelMixin

# Create your models here.


class Product(BaseEnterpriseAuditModelMixin):
    """Defines the global catalog (e.g., Broiler Meat, Organic Eggs)."""

    name = models.CharField(_("Product Name"), max_length=100, unique=True)
    category = models.CharField(
        _("Category"), max_length=50, choices=ProductCategory.choices
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


class ProductVariant(BaseEnterpriseAuditModelMixin):
    """
    Combines the parent Product with specific physical attributes, pricing, and SKU.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
        verbose_name=_("Parent Product"),
    )

    cut_type = models.CharField(
        _("Cut Type"),
        max_length=20,
        choices=MeatCutType.choices,
        default=MeatCutType.WHOLE,
    )
    storage_state = models.CharField(
        _("Storage State"),
        max_length=20,
        choices=StorageState.choices,
        default=StorageState.FRESH,
    )
    fat_level = models.CharField(
        _("Fat Content"),
        max_length=20,
        choices=FatLevel.choices,
        default=FatLevel.MEDIUM,
    )

    sku = models.CharField(
        _("SKU / Item Code"), max_length=100, unique=True, db_index=True
    )
    price = MoneyField(
        _("Unit Price"), max_digits=12, decimal_places=2, default_currency="TZS"
    )

    is_active = models.BooleanField(_("Is Available for Sale"), default=True)
    variant_metadata = models.JSONField(_("Variant Metadata"), default=dict, blank=True)

    class Meta:
        db_table = "product_variant"
        verbose_name = _("Product Variant")
        verbose_name_plural = _("Product Variants")
        unique_together = ("product", "cut_type", "storage_state", "fat_level")

    def __str__(self):
        return f"{self.product.name} - {self.get_cut_type_display()} [{self.get_storage_state_display()}]"


class PackagedProduct(BaseEnterpriseAuditModelMixin):
    """Specific items ready for retail tagged to their architectural variants."""

    session = models.ForeignKey(
        "ppms.ProcessingSession", on_delete=models.CASCADE, related_name="packages"
    )

    variant_ref = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        verbose_name=_("Product Variant Reference"),
        related_name="packages",
    )
    production_line = models.CharField(
        _("Production Line"), max_length=50, db_index=True, blank=True
    )

    label_code = models.CharField(
        _("QR/Barcode"), max_length=100, unique=True, db_index=True
    )
    weight = models.DecimalField(
        _("Unit Weight (KG)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    units_inside_package = models.PositiveIntegerField(
        _("Pieces Inside Package"), default=1
    )
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

    def clean(self):
        """Ensures packaged weight doesn't exceed the processing session yield capacity."""
        try:
            locked_session = ProcessingSession.objects.select_for_update().get(
                pk=self.session_id
            )
        except ProcessingSession.DoesNotExist:
            raise ValidationError(_("Processing Session inayorejelewa haipo."))

        existing_pkg_weight = PackagedProduct.objects.filter(
            session=locked_session
        ).exclude(pk=self.pk).aggregate(total=models.Sum("weight"))["total"] or Decimal(
            "0.00"
        )

        if (existing_pkg_weight + self.weight) > locked_session.total_dressed_weight:
            raise ValidationError(
                _(
                    f"Traceability Error: Uzito wa pakiti unazidi uzito wa "
                    f"mzoga uliopo kwenye session hii ({locked_session.total_dressed_weight}kg)."
                )
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.label_code} - {self.product_stock_ref.product_name}"

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
