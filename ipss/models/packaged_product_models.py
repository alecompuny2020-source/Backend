from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.choices import PackageStatus
from common.mixins import BaseEnterpriseAuditModelMixin

# Create your models here.


class PackagedProduct(BaseEnterpriseAuditModelMixin):
    """Specific items ready for retail tagged to their architectural variants."""

    session = models.ForeignKey(
        "ppms.ProcessingSession", on_delete=models.CASCADE, related_name="packages"
    )

    variant_ref = models.ForeignKey(
        "ipss.ProductVariant",
        on_delete=models.CASCADE,
        verbose_name=_("Product Variant Reference"),
        related_name="packages",
    )
    production_line = models.CharField(
        _("Production Line"),
        max_length=50,
        db_index=True,
        blank=True,
        help_text=_(
            "Kitambulisho cha mstari wa uzalishaji/usindikaji. "
            "Husaidia kufuatilia ufanisi wa mashine na timu iliyokuwa zamu."
        ),
    )
    status = models.CharField(
        max_length=20,
        choices=PackageStatus.choices,
        default=PackageStatus.IN_STOCK,
        db_index=True,
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
