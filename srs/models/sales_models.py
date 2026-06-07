from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from phonenumber_field.modelfields import PhoneNumberField

from common.choices import (
    ItemDisposition,
    PaymentMethod,
    SaleInvoiceStatus,
    UnitOfMeasure,
    current_time,
)
from common.mixins import BaseEnterpriseAuditModelMixin, BaseEnterpriseModelMixin

# Create your models here.


class Sale(BaseEnterpriseAuditModelMixin):
    """The finalized transaction record."""

    order = models.OneToOneField(
        "srs.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sale_record",
    )
    sales_type = models.CharField(max_length=30, default="direct")
    total_amount = MoneyField(max_digits=15, decimal_places=2, default_currency="TZS")
    sales_outlet = models.ForeignKey(
        "ipss.StorageUnit",
        on_delete=models.SET_NULL,
        null=True,
        related_name="office_sales",
    )
    status = models.CharField(max_length=20, choices=SaleInvoiceStatus.choices)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    payment_status = models.CharField(
        max_length=20,
        choices=SaleInvoiceStatus.choices,
        default=SaleInvoiceStatus.PENDING,
    )

    # Metadata includes: {
    #     'tax_breakdown': {'vat': 18.00, 'levy': 2.00},
    #     'client_ip': '192.168.1.1',
    #     'device': 'Mobile App',
    #     'discount_code_used': 'SUMMER2026'
    # }

    metadata = models.JSONField(_("Sale Metadata"), default=dict, blank=True)

    class Meta:
        db_table = "sale_transaction"
        ordering = ["-created_on"]
        indexes = [
            models.Index(fields=["sales_outlet", "created_on"]),
            models.Index(fields=["created_by"]),
            GinIndex(fields=["metadata"], name="sales_metadata_gin_idx"),
        ]

    @property
    def amount_paid(self):
        return self.payments.aggregate(total=models.Sum("amount"))["total"] or Decimal(
            "0.00"
        )

    @property
    def balance_due(self):
        return self.total_amount - self.amount_paid

    def update_status(self):
        """Logic to handle partial vs full payments."""
        paid = self.amount_paid
        if paid >= self.total_amount:
            self.status, self.payment_status = "PAID", "PAID"
        elif paid > 0:
            self.status, self.payment_status = "PARTIAL", "PARTIAL"
        else:
            self.status, self.payment_status = "PENDING", "PENDING"
        self.save()

        if self.order:
            if self.status == "PAID":
                self.order.order_status = "PAID"
            elif self.status == "PARTIAL":
                self.order.order_status = "PARTIAL_PAID"

            self.order.save()

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Sale '{self.id}' "
                f"from: {old_data} to: total {self.total_amount}, status {self.status}, payment {self.payment_status}"
            )
        return (
            f"Recorded Sale '{self.id}' linked to Order '{self.order.order_number if self.order else 'N/A'}' "
            f"total {self.total_amount}, status {self.status}, payment {self.payment_status}, method {self.payment_method}"
        )

    def __str__(self):
        return f"Sale #{self.id} - {self.sale_date.date()}"


class SaleItem(BaseEnterpriseModelMixin):
    """Line item detail with automatic total calculation."""

    sale = models.ForeignKey(Sale, related_name="items", on_delete=models.CASCADE)
    product_stock = models.ForeignKey(
        "ipss.ProductStock", on_delete=models.CASCADE, blank=True, null=True
    )
    packaged_product = models.ForeignKey(
        "ipss.PackagedProduct", on_delete=models.PROTECT, blank=True, null=True
    )
    quantity = models.PositiveIntegerField()
    unit_price = MoneyField(max_digits=15, decimal_places=2, default_currency="TZS")
    unit_measure = models.CharField(
        max_length=50, default="pc", choices=UnitOfMeasure.choices
    )
    discount = MoneyField(max_digits=15, decimal_places=2, default_currency="TZS")
    line_total = MoneyField(max_digits=15, decimal_places=2, default_currency="TZS")
    item_disposition = models.CharField(
        max_length=20, choices=ItemDisposition.choices, default=ItemDisposition.SOLD
    )
    attributes = models.JSONField(
        _("Product Attributes at Sale"), default=dict, blank=True
    )

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Sale Item for Sale '{self.sale.id}' "
                f"from: {old_data} to: product {self.product}, quantity {self.quantity}, line total {self.line_total}"
            )
        return (
            f"Added Sale Item to Sale '{self.sale.id}' "
            f"product {self.product}, quantity {self.quantity}, line total {self.line_total}, disposition {self.item_disposition}"
        )

    def clean(self):
        if not self.product_stock and not self.packaged_product:
            raise ValidationError(
                "Lazima uchague bidhaa kutoka kwenye Stoki ya Jumla au Pakiti halisi."
            )

        if self.product_stock and self.packaged_product:
            raise ValidationError(
                "Huwezi kuuza stoki ya jumla na pakiti kwenye mstari mmoja. Tenganisha."
            )

    def save(self, *args, **kwargs):
        self.clean()
        self.line_total = (self.unit_price * self.quantity) - self.discount
        super().save(*args, **kwargs)

    class Meta:
        db_table = "sale_item"
        # unique_together = ("sale", "product")
        indexes = [GinIndex(fields=["attributes"], name="attributes_gin_idx")]
