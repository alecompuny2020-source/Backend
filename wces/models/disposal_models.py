from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.mixins import BaseEnterpriseAuditModelMixin

# Create your models here.


class DisposalArea(BaseEnterpriseAuditModelMixin):
    """It store the areas where waste will be disposed"""

    name = models.CharField(_("Location name"), max_length=100, unique=True)

    # Blueprint for financial_logic:
    # {
    #   "revenue_per_kg": 500.00,
    #   "disposal_cost_per_kg": 0.00,
    #   "currency": "TZS",
    #   "tax_category": "Zero-Rated"
    # }
    disposal_metadata = models.JSONField(
        _("Disposal Metadata"),
        default=dict,
    )
    is_active = models.BooleanField(_("Is Active"), default=True)

    class Meta:
        db_table = "disposal_area"
        verbose_name = _("Disposal Area")
        verbose_name_plural = _("Disposal Areas")
        indexes = [
            GinIndex(fields=["disposal_metadata"], name="disposal_metadata_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Disposal Area '{self.name}' "
                f"from: {old_data} to: metadata {self.disposal_metadata}"
            )
        return (
            f"Created Disposal Area '{self.name}' "
            f"with metadata {self.disposal_metadata}, active: {self.is_active}"
        )

    def __str__(self):
        return self.name


class WasteOutflow(BaseEnterpriseAuditModelMixin):
    """
    Tracks the final destination and financial outcome of waste.
    """

    collection_logs = models.ManyToManyField(
        "wces.WasteCollection",
        related_name="outflows",
        verbose_name=_("Linked Collections"),
    )
    destination = models.ForeignKey(DisposalArea, on_delete=models.RESTRICT)

    total_weight = models.DecimalField(
        _("Total Outflow Weight (KG)"), max_digits=15, decimal_places=2
    )

    # Blueprint for exit_metadata:
    # {
    #   "receipt_no": "W-102",
    #   "transport_cost": 20000.00,
    #   "sale_revenue": 50000.00,
    #   "currency": "TZS",
    #   "buyer_contact": "+255...",
    #   "vehicle_plate": "T 123 ABC"
    # }
    exit_metadata = models.JSONField(
        _("Exit Audit Metadata"),
        default=dict,
        help_text=_("Tracks transport costs, sale revenue, and buyer/logistics info."),
    )

    class Meta:
        db_table = "waste_audit"
        verbose_name = _("Waste Outflow Audit")
        ordering = ["-created_on"]
        indexes = [
            GinIndex(fields=["exit_metadata"], name="waste_exit_meta_gin_idx"),
        ]

    def validate_mass_balance(self):
        """
        HELPER: Ensures we aren't disposing of more than we collected.
        """
        sum_collected = sum(log.quantity_kg for log in self.collection_logs.all())
        if self.total_weight > sum_collected:
            raise ValidationError(
                {
                    "total_weight": _(
                        f"Outflow weight ({self.total_weight}kg) exceeds total collected ({sum_collected}kg)."
                    )
                }
            )

    def save(self, *args, **kwargs):
        # We check mass balance only if the record already exists (M2M requires an ID)
        if self.pk:
            self.validate_mass_balance()
        super().save(*args, **kwargs)

    @property
    def net_financial_impact(self) -> float:
        """
        Calculates if this waste movement made money or cost money.
        Extracts values from exit_metadata JSON.
        Calculates profit/loss from the waste transaction.
        """
        revenue = self.exit_metadata.get("sale_revenue", 0.00)
        costs = self.exit_metadata.get("transport_cost", 0.00)
        return float(revenue) - float(costs)

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Waste Outflow to '{self.destination.name}' "
                f"from: {old_data} to: total {self.total_weight}kg, "
                f"net impact {self.net_financial_impact}"
            )
        return (
            f"Recorded Waste Outflow to '{self.destination.name}' "
            f"— total {self.total_weight}kg, net impact {self.net_financial_impact}, "
            f"metadata: {self.exit_metadata}"
        )
