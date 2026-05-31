from decimal import Decimal

from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from common.choices import SourceChoices
from common.mixins import BaseEnterpriseAuditModelMixin

# Create your models here.


class FeedConsumption(BaseEnterpriseAuditModelMixin):
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
        "fns.FeedType", on_delete=models.PROTECT, verbose_name=_("Feed Type")
    )
    quantity_used_kg = models.DecimalField(
        _("Quantity Used (KG)"), max_digits=10, decimal_places=2
    )
    waste_amount_kg = models.DecimalField(
        _("Waste Amount (KG)"), max_digits=10, decimal_places=2, default=0.00
    )
    water_liters_added = models.DecimalField(
        _("Water Intake (Liters)"), max_digits=10, decimal_places=2, default=0.00
    )

    # Blueprint for consumption_notes:
    # {
    #   "waste_kg": 2.5,
    #   "feeder_status": "Clean",
    #   "water_liters_added": 50,
    #   "abnormal_feeding_behavior": false
    # }
    consumption_notes = models.JSONField(
        _("Consumption Notes"),
        default=dict,
        blank=True,
        help_text=_("Stores waste data, feeder status, and behavioral observations."),
    )

    class Meta:
        db_table = "feed_consumption"
        unique_together = ("batch", "created_on", "feed_type")
        ordering = ["-created_on"]
        verbose_name = _("Feed Consumption Log")
        indexes = [
            GinIndex(fields=["consumption_notes"], name="feed_usage_notes_gin_idx"),
        ]

        permissions = [
            ("update_water_intake", "Can update water intake"),
            ("view_kpi_dashboard", "Can view KPI dashboard"),
        ]

    @property
    def actual_intake(self) -> float:
        """Calculates what the birds actually ate safely."""
        return max(Decimal("0.00"), self.quantity_used_kg - self.waste_amount_kg)

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Saves logs and dynamically adjusts physical warehouse inventory."""

        if self._state.adding:
            quantity_delta = self.quantity_used_kg
        else:
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

            if inventory.total_quantity_kg < quantity_delta:
                raise ValidationError(
                    _(
                        f"Inventory Shortage: Ghala lina kilo {inventory.total_quantity_kg} tu za {self.feed_type.name}."
                    )
                )

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
