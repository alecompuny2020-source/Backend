from django.db import models, transaction
from common.mixins import BaseEnterpriseAuditModelMixin
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from common.choices import current_time, CustomerType


# Create your models here.

class ReturnRequest(models.Model):
    """ Handles item returns. Links back to the original Sale. """

    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name="returns")
    sale_item = models.ForeignKey(SaleItem, on_delete=models.CASCADE)
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("APPROVED", "Approved"),
            ("COMPLETED", "Completed"),
        ],
    )
    disposition = models.CharField(
        max_length=20, choices=ItemDisposition.choices
    )  # e.g., 'DAMAGED'
    processed_at = models.DateTimeField()

    metadata = models.JSONField(
        default=dict,
        help_text="{'restock_warehouse_id': 1, 'refund_transaction_id': '...', 'approved_by': 'Manager'}",
    )

    class Meta:
        db_table = "return_request"

    def clean(self):
        """
        ERP-Level Validation: Cross-references Sale and SaleItem.
        """
        # 1. Ensure the item actually belongs to the claimed Sale
        if self.sale_item.sale != self.sale:
            raise ValidationError(
                _(
                    f"Security Alert: Item {self.sale_item.product.name} "
                    f"was not part of Sale {self.sale.id}."
                )
            )

        # 2. Prevent returning more than what was purchased
        if self.quantity_returned > self.sale_item.quantity:
            raise ValidationError(
                _(
                    f"Quantity Error: Customer bought {self.sale_item.quantity} "
                    f"units, but is trying to return {self.quantity_returned}."
                )
            )

        # 3. Check for previous returns (prevent double-dipping)
        # Sum all completed returns for this specific sale item
        previous_returns = (
            ReturnRequest.objects.filter(sale_item=self.sale_item, status="COMPLETED")
            .exclude(pk=self.pk)
            .aggregate(total=models.Sum("quantity_returned"))["total"]
            or 0
        )

        if (previous_returns + self.quantity_returned) > self.sale_item.quantity:
            raise ValidationError(
                _(
                    f"Fraud Prevention: Total returned units would exceed original purchase count."
                )
            )

    def save(self, *args, **kwargs):
        """Final validation check before database commit."""
        self.full_clean()
        if self.status == "COMPLETED" and not self.processed_at:
            self.processed_at = timezone.now()
        super().save(*args, **kwargs)
        

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Return Request for Sale '{self.sale.id}' "
                f"from: {old_data} to: item {self.sale_item.product}, quantity {self.quantity_returned}, status {self.status}"
            )
        return (
            f"Created Return Request for Sale '{self.sale.id}' "
            f"item {self.sale_item.product}, quantity {self.quantity_returned}, reason {self.reason}, status {self.status}"
        )



class CreditNote(BaseEnterpriseAuditModelMixin):
    """
    Tracks returns or overpayments that result in store credit.
    Essential for Wholesale/B2B relationships.
    """

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="credit_notes"
    )
    amount = MoneyField(max_digits=15, decimal_places=2, default_currency="TZS")
    reason = models.TextField()
    is_redeemed = models.BooleanField(default=False)
    metadata = models.JSONField(
        default=dict, blank=True
    )  # { "original_sale_id": "UUID", "approved_by": "ID" }

    class Meta:
        db_table = "customer_credit_note"
        indexes = [
            GinIndex(fields=["metadata"], name="metadata_gin_idx")
        ]

    @classmethod
    @transaction.atomic
    def create_from_return(cls, return_request):
        """
        AUTOMATION: Generates a Credit Note directly from an approved Return.
        Called by the ReturnRequest system.
        """
        # Calculate value: quantity * unit_price (from the snapshot)
        unit_price = Decimal(
            return_request.sale_item.pricing_snapshot.get("unit_price_at_sale", 0)
        )
        credit_value = return_request.quantity_returned * unit_price

        note = cls.objects.create(
            customer=return_request.sale.offline_customer,
            amount=credit_value,
            reason=f"Return of {return_request.sale_item.product.name}: {return_request.reason}",
            metadata={
                "return_request_id": str(return_request.id),
                "original_sale_id": str(return_request.sale.id),
                "approved_by": str(
                    return_request.approved_by.id
                    if return_request.approved_by
                    else "System"
                ),
            },
        )
        return note

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Credit Note for Customer '{self.customer.name}' "
                f"from: {old_data} to: amount {self.amount}, reason {self.reason}, redeemed {self.is_redeemed}"
            )
        return (
            f"Issued Credit Note for Customer '{self.customer.name}' "
            f"amount {self.amount}, reason {self.reason}, redeemed {self.is_redeemed}"
        )

    def __str__(self):
        status = "Redeemed" if self.is_redeemed else "Available"
        return f"Credit for {self.customer.name}: {self.amount} TZS ({status})"
