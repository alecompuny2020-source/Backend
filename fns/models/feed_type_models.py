from decimal import Decimal

from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from common.choices import SourceChoices
from common.mixins import BaseEnterpriseAuditModelMixin

# Create your models here.


class FeedType(BaseEnterpriseAuditModelMixin):
    """Defines the nutritional profile and pricing of feed."""

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
        default=SourceChoices.FARM_PRODUCED,
    )

    # Blueprint for composition (Nutritional specs):
    # {
    #   "protein_pct": 22.0,
    #   "metabolizable_energy_kcal": 3000,
    #   "calcium_pct": 1.0,
    #   "lysine_pct": 1.2,
    #   "is_medicated": true
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
        return f"{self.name} ({self.get_feed_source_display()})"
