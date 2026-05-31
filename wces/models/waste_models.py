from django.db import models
from common.mixins import BaseEnterpriseAuditModelMixin
from django.contrib.postgres.indexes import GinIndex
from django.utils.translation import gettext_lazy as _
from common.choices import WasteDisposalMethod

# Create your models here.

class WasteCategory(BaseEnterpriseAuditModelMixin):
    """
    Defines types of waste: ORGANIC (Manure), HAZARDOUS (Medical), PLASTIC, etc.
    Links waste types to their financial and safety logic.
    """

    name = models.CharField(_("Waste Type Name"), max_length=100, unique=True)
    disposal_method = models.CharField(
        _("Primary Disposal Method"), max_length=50, choices=WasteDisposalMethod.choices,
        default = WasteDisposalMethod.RECYCLE
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



class WasteCollection(BaseEnterpriseAuditModelMixin):
    """
    Daily Kiosk Log: Records waste generation at the source (Sheds or Rental Units).
    Essential for farm hygiene audits.
    """

    location = models.ForeignKey(
        'sfap.Farm',
        on_delete=models.CASCADE,
        related_name="waste_collections",
        verbose_name=_("Farm Location"),
    )
    category = models.ForeignKey(
        WasteCategory, on_delete=models.PROTECT, verbose_name=_("Waste Category")
    )

    # Source identification using string references to prevent circular imports
    source_batch = models.ForeignKey(
        'sfap.Batch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="waste_produced",
    )
    # source_unit = models.ForeignKey(
    #     "core.RentalUnit",
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name="waste_produced",
    # )

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
