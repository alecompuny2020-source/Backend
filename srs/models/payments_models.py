from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from phonenumber_field.modelfields import PhoneNumberField

from common.choices import now

# Create your models here.


class Payment(models.Model):
    """Records payment events and triggers Sale status updates."""

    sale = models.ForeignKey(
        "srs.Sale", on_delete=models.CASCADE, related_name="payments"
    )
    date_paid = models.DateTimeField(default=now)
    amount = MoneyField(max_digits=15, decimal_places=2, default_currency="TZS")
    method = models.ForeignKey("core.PaymentMethod", on_delete=models.RESTRICT)
    transaction_reference = models.CharField(max_length=100, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.sale.update_status()

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Payment for Sale '{self.sale.id}' "
                f"from: {old_data} to: amount {self.amount}, method {self.method}, reference {self.reference_id}"
            )
        return (
            f"Recorded Payment for Sale '{self.sale.id}' "
            f"amount {self.amount}, method {self.method}, reference {self.reference_id}"
        )
