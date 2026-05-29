from django.db import models, transaction
from django.contrib.postgres.indexes import GinIndex
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from django.core.exceptions import ValidationError
from decimal import Decimal
from common.mixins import BaseEnterpriseAuditModelMixin
from common.choices import SourceChoices

# Create your models here.


class FeedInventory(BaseEnterpriseAuditModelMixin):
    """ Tracks stock levels in silos or warehouses. """

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

    # Blueprint for stock_logs (Arrival history):
    # [
    #   {
    #     "date": "2026-02-01",
    #     "qty_received": 500.0,
    #     "expiry_date": "2026-08-01",
    #     "supplier_invoice": "INV-9982",
    #     "batch_number": "BATCH-X-01"
    #   }
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
            return (
                f"Updated Feed Inventory for '{self.feed_type.name}' "
                f"from total: {old_data.get('total_quantity_kg')}kg "
                f"to: {self.total_quantity_kg}kg"
            )
        return (
            f"Created Feed Inventory for '{self.feed_type.name}' "
            f"with {self.total_quantity_kg}kg in stock (Reorder level: {self.reorder_level}kg)"
        )

    def __str__(self):
        return f"{self.feed_type.name} - {self.total_quantity_kg}kg"
