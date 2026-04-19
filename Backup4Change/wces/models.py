from django.db import models
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.utils.translation import gettext_lazy as _
from ..helpers import CURRENCY_CHOICES, DISPOSAL_METHOD_CHOICES
from ..utils import FarmAuditBaseModel

# Create your models here.

class WasteCategory(FarmAuditBaseModel):
    """
    Defines types of waste: ORGANIC (Manure), HAZARDOUS (Medical), PLASTIC, etc.
    Links waste types to their financial and safety logic.
    """

    name = models.CharField(_("Waste Type Name"), max_length=100, unique=True)
    disposal_method = models.CharField(
        _("Primary Disposal Method"), max_length=50, choices=DISPOSAL_METHOD_CHOICES
    )

    # Blueprint for financial_logic:
    # {
    #   "revenue_per_kg": 500.00,
    #   "disposal_cost_per_kg": 0.00,
    #   "currency": "TZS",
    #   "tax_category": "Zero-Rated"
    # }
    financial_logic = models.JSONField(
        _("Financial Logic"),
        default=dict,
        help_text=_("Stores pricing for sales or costs for disposal per unit."),
    )

    requires_special_handling = models.BooleanField(
        _("Hazardous / Special Handling"),
        default=False,
        help_text=_("If true, requires specific safety protocols for collection."),
    )

    class Meta:
        db_table = "waste_category"
        verbose_name = _("Waste Category")
        verbose_name_plural = _("Waste Categories")
        indexes = [
            GinIndex(fields=["financial_logic"], name="waste_fin_logic_gin_idx"),
        ]

    # def clean(self):
    #     """Ensure financial logic contains required currency keys."""
    #     if self.financial_logic and 'currency' not in self.financial_logic:
    #         raise ValidationError(_("Financial logic must specify a currency."))

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Waste Category '{self.name}' "
                f"from: {old_data} to: disposal method {self.disposal_method}, "
                f"financial logic {self.financial_logic}"
            )
        return (
            f"Created Waste Category '{self.name}' "
            f"with disposal method {self.disposal_method}, "
            f"special handling required: {self.requires_special_handling}"
        )

    def __str__(self):
        return self.name


class WasteCollection(FarmAuditBaseModel):
    """
    Daily Kiosk Log: Records waste generation at the source (Sheds or Rental Units).
    Essential for farm hygiene audits.
    """

    location = models.ForeignKey(
        settings.FARM_REFERENCE,
        on_delete=models.CASCADE,
        related_name="waste_collections",
        verbose_name=_("Farm Location"),
    )
    category = models.ForeignKey(
        WasteCategory, on_delete=models.PROTECT, verbose_name=_("Waste Category")
    )

    # Source identification using string references to prevent circular imports
    source_batch = models.ForeignKey(
        settings.BATCH_REFERENCE,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="waste_produced",
    )
    source_unit = models.ForeignKey(
        "core.RentalUnit",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="waste_produced",
    )

    quantity_kg = models.DecimalField(
        _("Quantity (KG)"), max_digits=12, decimal_places=2
    )

    # Blueprint for collection_details:
    # {
    #   "is_segregated": true,
    #   "moisture_content": "15%",
    #   "recorded_by_kiosk_id": "KIOSK_IHUMWA_01",
    #   "odour_level": "Low"
    # }
    collection_details = models.JSONField(
        _("Collection Metadata"),
        default=dict,
        blank=True,
        help_text=_(
            "Stores physical properties and audit data from the point of collection."
        ),
    )

    class Meta:
        db_table = "waste_colleaction"
        verbose_name = _("Waste Collection Log")
        ordering = ["-created_on"]
        indexes = [
            GinIndex(fields=["collection_details"], name="waste_coll_meta_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Waste Collection at '{self.location}' "
                f"from: {old_data} to: {self.quantity_kg}kg of {self.category.name}"
            )
        source = (
            self.source_batch.batch_id if self.source_batch else self.source_unit.id
        )
        return (
            f"Recorded Waste Collection at '{self.location}' "
            f"— {self.quantity_kg}kg of {self.category.name}, source: {source}, "
            f"details: {self.collection_details}"
        )

    def clean(self):
        """Validation: Waste must belong to either a Batch or a Rental Unit, not both or neither."""
        if not self.source_batch and not self.source_unit:
            raise ValidationError(
                _("Waste must be linked to a source (Batch or Rental Unit).")
            )
        if self.source_batch and self.source_unit:
            raise ValidationError(
                _(
                    "Waste cannot be linked to both a Batch and a Rental Unit simultaneously."
                )
            )

        if self.quantity_kg <= 0:
            raise ValidationError(_("Quantity must be greater than zero."))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class DisposalArea(FarmAuditBaseModel):
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


class WasteOutflow(FarmAuditBaseModel):
    """
    Tracks the final destination and financial outcome of waste.
    """

    collection_logs = models.ManyToManyField(
        WasteCollection, related_name="outflows", verbose_name=_("Linked Collections")
    )
    destination = models.ForeignKey(DisposalArea, on_delete=models.CASCADE)

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

    @property
    def net_financial_impact(self):
        """
        Calculates if this waste movement made money or cost money.
        Extracts values from exit_metadata JSON.
        Calculates profit/loss from the waste transaction.
        """
        revenue = self.exit_metadata.get("sale_revenue", 0.00)
        costs = self.exit_metadata.get("transport_cost", 0.00)
        return float(revenue) - float(costs)

    def save(self, *args, **kwargs):
        # We check mass balance only if the record already exists (M2M requires an ID)
        if self.pk:
            self.validate_mass_balance()
        super().save(*args, **kwargs)
