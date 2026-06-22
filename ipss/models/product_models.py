from decimal import Decimal

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from common.mixins import BaseEnterpriseAuditModelMixin

# Create your models here.


class Product(BaseEnterpriseAuditModelMixin):
    """Defines the global catalog (e.g., Broiler Meat, Organic Eggs)."""

    name = models.CharField(_("Product Name"), max_length=100, unique=True)
    category = models.ForeignKey("config.ProductCategory", on_delete=models.RESTRICT)
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
    cut_type = models.ForeignKey("config.MeatCutType", on_delete=models.RESTRICT)
    storage_state = models.ForeignKey("config.StorageState", on_delete=models.RESTRICT)
    fat_level = models.ForeignKey("config.FatLevel", on_delete=models.RESTRICT)

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
