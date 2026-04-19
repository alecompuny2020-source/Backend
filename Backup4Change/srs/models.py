from django.db import models, transaction
import uuid
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from phonenumber_field.modelfields import PhoneNumberField
from ..helpers import (
    CUSTOMER_TYPE, ITEM_DISPOSITION_CHOICES, ORDER_STATUS,
    PAYMENT_METHOD_CHOICES, SALE_STATUS_CHOICES,UNIT_CHOICES
    )
from ..utils import FarmAuditBaseModel

# Create your models here.

class Promotion(FarmAuditBaseModel):
    """
    Handles coupons, seasonal discounts, and buy-one-get-one (BOGO) logic.
    """

    code = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    discount_type = models.CharField(
        max_length=20, choices=[("PERCENT", "Percentage"), ("FIXED", "Fixed Amount")]
    )
    value = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(null=True, blank=True)

    # JSON for complex logic: {"min_order_value": 50000, "applicable_categories": ["Electronics"]}
    rules = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "promotion"

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Promotion '{self.code}' "
                f"from: {old_data} to: {self.discount_type} {self.value}, valid {self.valid_from}–{self.valid_to}"
            )
        return (
            f"Created Promotion '{self.code}' — {self.discount_type} {self.value}, "
            f"valid {self.valid_from}–{self.valid_to}, rules {self.rules}"
        )

    @property
    def is_active(self):
        now = timezone.now()
        return self.valid_from <= now <= self.valid_to


class Customer(FarmAuditBaseModel):
    """
    Manages RETAIL, WHOLESALE (Hotels), and DISTRIBUTOR entities.
    Central to the CRM and Account Receivables.
    """

    name = models.CharField(_("Customer Name"), max_length=255)
    customer_type = models.CharField(
        _("Type"), max_length=20, choices=CUSTOMER_TYPE, default="RETAIL"
    )
    contact_phone = PhoneNumberField(_("Contact Phone"))
    email = models.EmailField(_("Email Address"), blank=True)

    # Blueprint for customer_profile:
    # {
    #   "lat": -6.7, "long": 39.2,
    #   "preferred_delivery_time": "Morning",
    #   "tax_id": "123-456-789",
    #   "tin_number": "TIN-990-11"
    # }
    customer_profile = models.JSONField(_("Profile Metadata"), default=dict, blank=True)
    credit_limit = models.DecimalField(
        _("Credit Limit"), max_digits=15, decimal_places=2, default=0.00
    )
    is_active = models.BooleanField(_("Is Active"), default=True)

    class Meta:
        db_table = "customer"
        verbose_name = _("Customer")
        ordering = ["name"]
        indexes = [
            GinIndex(fields=["customer_profile"], name="customer_profile_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Customer '{self.name}' "
                f"from: {old_data} to: type {self.customer_type}, credit limit {self.credit_limit}, active {self.is_active}"
            )
        return (
            f"Registered Customer '{self.name}' "
            f"type {self.customer_type}, credit limit {self.credit_limit}, active {self.is_active}"
        )

    def get_full_name(self):
        """Returns string representation of the user as what he or she filled"""
        return self.name.title() if self.name else self.email

    def __str__(self):
        return self.get_full_name()


class Order(FarmAuditBaseModel):
    """
    The financial contract for a sale.
    Links the customer to the revenue and assigns the delivery agent.
    """

    order_number = models.CharField(
        _("Order ID"), max_length=50, unique=True, db_index=True
    )
    offline_customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="orders", null=True, blank=True
    )
    online_customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    subtotal = MoneyField(
        verbose_name=_("Subtotal"),
        max_digits=15,
        decimal_places=2,
        default_currency="TZS",
    )
    discount_amount = MoneyField(
        verbose_name=_("Discount"),
        max_digits=15,
        decimal_places=2,
        default=0,
        default_currency="TZS",
    )
    total_payable = MoneyField(
        verbose_name=_("Total Payable"),
        max_digits=15,
        decimal_places=2,
        default_currency="TZS",
    )

    status = models.CharField(
        _("Status"), max_length=20, choices=ORDER_STATUS, default="PENDING"
    )

    # Blueprint for order_history (Audit Trail):
    # [{"status": "Confirmed", "time": "2026-02-24T10:00Z", "user_id": 4, "note": "Payment verified"}]
    internal_notes = models.JSONField(_("Order History Log"), default=list)

    class Meta:
        db_table = "sales_order"
        verbose_name = _("Sales Order")
        ordering = ["-created_on"]
        indexes = [
            GinIndex(fields=["internal_notes"], name="sales_order_notes_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Order '{self.order_number}' "
                f"from: {old_data} to: subtotal {self.subtotal}, discount {self.discount_amount}, "
                f"total payable {self.total_payable}, status {self.status}"
            )
        return (
            f"Created Order '{self.order_number}' for {self.get_order_owner()} "
            f"subtotal {self.subtotal}, discount {self.discount_amount}, total payable {self.total_payable}, status {self.status}"
        )

    def clean(self):
        """Ensures that the order is attached to exactly one customer type."""
        if not self.offline_customer and not self.online_customer:
            raise ValidationError(
                _("Order must be associated with either an offline or online customer.")
            )
        if self.offline_customer and self.online_customer:
            raise ValidationError(
                _(
                    "Order cannot be associated with both offline and online customers simultaneously."
                )
            )

    def get_order_owner(self):
        """Returns string representation of the owner"""

        if self.offline_customer:
            return self.offline_customer.get_full_name()
        if self.online_customer:
            return self.online_customer.get_full_name()
        return _("Unknown Customer")

    def save(self, *args, **kwargs):
        self.total_payable = self.subtotal - self.discount_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_number} - {self.get_order_owner()}"


class OrderItem(models.Model):
    """
    Snapshot of specific inventory items sold.
    Essential for calculating COGS (Cost of Goods Sold).
    """

    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product_stock = models.ForeignKey(
        settings.STOCK_PRODUCT_REFERENCE, on_delete=models.PROTECT
    )
    quantity = models.DecimalField(
        _("Quantity Sold"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    # Blueprint for pricing_snapshot:
    # {
    #   "unit_price_at_sale": 15000,
    #   "tax_rate": 0.18,
    #   "cost_price_at_sale": 11000,
    #   "unit": "KG"
    # }
    pricing_snapshot = models.JSONField(_("Pricing Snapshot"), default=dict)

    class Meta:
        db_table = "sales_item"
        verbose_name = _("Order Item")
        indexes = [
            GinIndex(fields=["pricing_snapshot"], name="order_item_price_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Order Item for Order '{self.order.order_number}' "
                f"from: {old_data} to: product {self.product_stock}, quantity {self.quantity}, pricing {self.pricing_snapshot}"
            )
        return (
            f"Added Order Item to Order '{self.order.order_number}' "
            f"product {self.product_stock}, quantity {self.quantity}, pricing {self.pricing_snapshot}"
        )


class Sale(FarmAuditBaseModel):
    """The finalized transaction record."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sale_record",
    )
    sales_type = models.CharField(max_length=30, default="direct")
    total_amount = MoneyField(max_digits=15, decimal_places=2, default_currency="TZS")
    sales_outlet = models.ForeignKey(
        "core.WarehouseLocation",
        on_delete=models.SET_NULL,
        null=True,
        related_name="office_sales",
    )
    status = models.CharField(max_length=20, choices=SALE_STATUS_CHOICES)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(
        max_length=20, choices=SALE_STATUS_CHOICES, default="PENDING"
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
        ]

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

    def __str__(self):
        return f"Sale #{self.id} - {self.sale_date.date()}"


class SaleItem(models.Model):
    """Line item detail with automatic total calculation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sale = models.ForeignKey(Sale, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(
        settings.STOCK_PRODUCT_REFERENCE, on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField()
    unit_price = MoneyField(max_digits=15, decimal_places=2, default_currency="TZS")
    unit_measure = models.CharField(max_length=50, default="pc", choices=UNIT_CHOICES)
    discount = MoneyField(max_digits=15, decimal_places=2, default_currency="TZS")
    line_total = MoneyField(max_digits=15, decimal_places=2, default_currency="TZS")
    item_disposition = models.CharField(
        max_length=20, choices=ITEM_DISPOSITION_CHOICES, default="SOLD"
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

    def save(self, *args, **kwargs):
        self.line_total = (self.unit_price * self.quantity) - self.discount
        super().save(*args, **kwargs)

    class Meta:
        db_table = "sale_item"
        unique_together = ("sale", "product")


class CreditNote(models.Model):
    """
    Tracks returns or overpayments that result in store credit.
    Essential for Wholesale/B2B relationships.
    """

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="credit_notes"
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    reason = models.TextField()
    is_redeemed = models.BooleanField(default=False)
    metadata = models.JSONField(
        default=dict, blank=True
    )  # { "original_sale_id": "UUID", "approved_by": "ID" }
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "customer_credit_note"

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


class Payment(models.Model):
    """Records payment events and triggers Sale status updates."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="payments")
    date_paid = models.DateTimeField(default=timezone.now)
    amount = MoneyField(max_digits=15, decimal_places=2, default_currency="TZS")
    method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    reference_id = models.CharField(max_length=100, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)

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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.sale.update_status()


class ReturnRequest(models.Model):
    """
    Handles item returns. Links back to the original Sale.
    """

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
        max_length=20, choices=ITEM_DISPOSITION_CHOICES
    )  # e.g., 'DAMAGED'
    approved_by = models.ForeignKey(
        settings.FARM_WORKER, on_delete=models.SET_NULL, null=True
    )
    processed_at = models.DateTimeField()

    metadata = models.JSONField(
        default=dict,
        help_text="{'restock_warehouse_id': 1, 'refund_transaction_id': '...'}",
    )

    class Meta:
        db_table = "return_request"

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


class DailySummary(models.Model):
    """Agent End-of-Day (EOD) closure for financial reconciliation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    closing_date = models.DateTimeField(db_index=True)
    sales_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_closures",
    )

    total_sales_count = models.IntegerField(default=0)
    total_revenue = MoneyField(max_digits=15, decimal_places=2, default_currency="TZS")
    total_cash_sales = MoneyField(
        max_digits=15, decimal_places=2, default_currency="TZS"
    )
    net_cash_settlement = MoneyField(
        max_digits=15, decimal_places=2, default_currency="TZS"
    )
    # Breakdown JSON includes: {
    #     'expenses': [{'category': 'Fuel', 'amount': 5000}],
    #     'cash_denominations': {'10k_notes': 5, '5k_notes': 10},
    #     'notes': "Slightly late closure due to high traffic"
    # }
    breakdown = models.JSONField(_("Financial Breakdown"), default=dict, blank=True)

    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="closures_managed",
    )
    closed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "daily_summary"
        unique_together = ("closing_date", "sales_agent")

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Daily Summary for Agent '{self.sales_agent}' "
                f"from: {old_data} to: total sales {self.total_sales_count}, revenue {self.total_revenue}, cash {self.total_cash_sales}"
            )
        return (
            f"Recorded Daily Summary for Agent '{self.sales_agent}' "
            f"date {self.closing_date}, total sales {self.total_sales_count}, revenue {self.total_revenue}, cash {self.total_cash_sales}"
        )
