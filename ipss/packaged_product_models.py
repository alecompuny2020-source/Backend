from django.db import models
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from common.mixins import BaseEnterpriseAuditModelMixin

# Create your models here.

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
