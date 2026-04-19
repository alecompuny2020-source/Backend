from django.db import models
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField

from ..utils import FarmAuditBaseModel
from ..helpers import CURRENCY_CHOICES, PAYMENT_METHOD_CHOICES

# Create your models here.

class AccountCategory(models.Model):
    """
    Module 5: Chart of Accounts.
    Categorizes transactions (e.g., Variable Costs, Fixed Costs, Revenue).
    """

    name = models.CharField(_("Category Name"), max_length=100, unique=True)
    code = models.CharField(
        _("Account Code"),
        max_length=10,
        unique=True,
        help_text=_("e.g., EXP-FEED, REV-EGGS, EXP-LABOR"),
    )
    is_expense = models.BooleanField(_("Is Expense"), default=True)

    class Meta:
        db_table = "account_category"
        verbose_name = _("Account Category")
        verbose_name_plural = _("Account Categories")

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Account Category '{self.code}' "
                f"from: {old_data} to: name {self.name}, expense flag {self.is_expense}"
            )
        return (
            f"Created Account Category '{self.code}' "
            f"name {self.name}, expense flag {self.is_expense}"
        )

    def __str__(self):
        return f"{self.code} - {self.name}"


class Transaction(FarmAuditBaseModel):
    """
    The General Ledger.
    The source of truth for all farm finances, normalized to link costs to specific Batches.
    """

    TRANSACTION_TYPE_CHOICES = [("INCOME", _("Income")), ("EXPENSE", _("Expense"))]

    transaction_id = models.CharField(
        _("Transaction Reference"), max_length=100, unique=True, db_index=True
    )
    category = models.ForeignKey(
        AccountCategory,
        on_delete=models.PROTECT,
        related_name="transactions",
        verbose_name=_("Category"),
    )
    type = models.CharField(_("Type"), max_length=10, choices=TRANSACTION_TYPE_CHOICES)

    amount = MoneyField(
        verbose_name=_("Amount"),
        max_digits=15,
        decimal_places=2,
        default_currency="TZS",
        # Optional: if you want to limit users to specific currencies
        currency_choices=settings.CURRENCY_CHOICES,
    )
    date = models.DateField(_("Transaction Date"), db_index=True)

    # Linking: Variable Cost (Batch) vs General Cost (Null)
    # Using string reference to 'core.Batch' to avoid circular imports
    batch = models.ForeignKey(
        settings.BATCH_REFERENCE,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="finances",
        verbose_name=_("Linked Batch (Optional)"),
    )

    # Blueprint for metadata:
    # {
    #   "payment_method": "M-Pesa",
    #   "receipt_url": "s3://wonderful-poultry/receipts/2026/02/rtx_01.pdf",
    #   "vendor_name": "Kibo Feeds Ltd",
    #   "exchange_rate_to_gbp": 0.0003,
    #   "tax_amount": 0.00,
    #   "verified_by_audit": true
    # }
    metadata = models.JSONField(
        _("Transaction Metadata"),
        default=dict,
        blank=True,
        help_text=_("Stores payment method, receipt links, and vendor details."),
    )

    class Meta:
        db_table = "transaction"
        ordering = ["-date"]
        verbose_name = _("Financial Transaction")
        indexes = [
            GinIndex(fields=["metadata"], name="metadata_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Transaction '{self.transaction_id}' "
                f"from: {old_data} to: category {self.category.name}, type {self.type}, "
                f"amount {self.amount}, date {self.date}, batch {self.batch.batch_id if self.batch else 'N/A'}"
            )
        return (
            f"Recorded Transaction '{self.transaction_id}' "
            f"category {self.category.name}, type {self.type}, amount {self.amount}, "
            f"date {self.date}, batch {self.batch.batch_id if self.batch else 'N/A'}"
        )

    def __str__(self):
        return f"{self.transaction_id} | {self.amount} {self.currency}"


class BatchProfitLoss(models.Model):
    """
    Optimized reporting table for high-speed API access.
    Aggregates financial performance per flock.
    """

    # Using string reference to 'core.Batch'
    batch = models.OneToOneField(
        settings.BATCH_REFERENCE,
        on_delete=models.CASCADE,
        related_name="pl_statement",
        verbose_name=_("Flock Batch"),
    )

    total_revenue = MoneyField(
        verbose_name=_("Total Revenue"),
        max_digits=15,
        decimal_places=2,
        default=0,
        default_currency="TZS",
    )
    total_expenses = MoneyField(
        verbose_name=_("Total Expenses"),
        max_digits=15,
        decimal_places=2,
        default=0,
        default_currency="TZS",
    )
    net_profit = MoneyField(
        verbose_name=_("Net Profit"),
        max_digits=15,
        decimal_places=2,
        default=0,
        default_currency="TZS",
    )

    # Blueprint for cost_breakdown:
    # {
    #   "feed_cost_tzs": 5000000,
    #   "medical_cost_tzs": 200000,
    #   "labor_allocated_tzs": 150000,
    #   "mortality_loss_valuation_tzs": 45000,
    #   "chick_purchase_cost_tzs": 1200000
    # }
    cost_breakdown = models.JSONField(
        _("Detailed Cost Breakdown"),
        default=dict,
        help_text=_("Aggregated expense categories for instant P&L reporting."),
    )

    last_updated = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "batch_profit_loss"
        verbose_name = _("Batch P&L Statement")
        indexes = [
            GinIndex(fields=["cost_breakdown"], name="pl_breakdown_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Batch P&L for Batch '{self.batch.batch_id}' "
                f"from: {old_data} to: revenue {self.total_revenue}, expenses {self.total_expenses}, "
                f"net profit {self.net_profit}, breakdown {self.cost_breakdown}"
            )
        return (
            f"Created Batch P&L for Batch '{self.batch.batch_id}' "
            f"revenue {self.total_revenue}, expenses {self.total_expenses}, "
            f"net profit {self.net_profit}, breakdown {self.cost_breakdown}"
        )

    def __str__(self):
        return f"P&L: {self.batch.batch_id}"


class Category(models.Model):
    """
    Detailed Expense Categorization (e.g., Feed Purchase, Vaccine Supply, Utility).
    Different from AccountCategory as this is for operational procurement.
    """

    name = models.CharField(_("Category Name"), max_length=100, unique=True)
    category_description = models.CharField(
        _("Description"), max_length=255, blank=True, null=True
    )

    class Meta:
        db_table = "expense_category"
        verbose_name = _("Expense Category")
        verbose_name_plural = _("Expense Categories")
        ordering = ["name"]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Expense Category '{self.name}' "
                f"from: {old_data} to: description '{self.category_description}'"
            )
        return (
            f"Created Expense Category '{self.name}' "
            f"description: '{self.category_description}'"
        )

    def __str__(self):
        return self.name


class Payee(models.Model):
    """
    Vendor/Supplier Management.
    Tracks who the farm pays (e.g., TANESCO, Kibo Feeds, Local Vet).
    """

    name = models.CharField(_("Payee/Vendor Name"), max_length=150)
    phone_number = PhoneNumberField(
        _("Contact Number"), region="TZ", db_index=True, null=True
    )

    address = models.CharField(
        max_length=255, null=True, verbose_name=_("Business Address")
    )

    # Blueprint for payee_metadata:
    # {
    #   "tin_number": "123-456-789",
    #   "vrn_number": "40012345X",
    #   "bank_details": {"bank": "CRDB", "account": "01J123..."},
    #   "is_active_supplier": true
    # }
    payee_metadata = models.JSONField(
        _("Vendor Metadata"),
        default=dict,
        blank=True,
        help_text=_("Stores Tax IDs (TIN/VRN) and banking details."),
    )

    class Meta:
        db_table = "payee"
        verbose_name = _("Payee/Vendor")
        verbose_name_plural = _("Payees/Vendors")
        ordering = ["name"]
        indexes = [
            GinIndex(fields=["payee_metadata"], name="payee_meta_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Payee '{self.name}' "
                f"from: {old_data} to: phone {self.phone_number}, address {self.address}, metadata {self.payee_metadata}"
            )
        return (
            f"Registered Payee '{self.name}' "
            f"phone {self.phone_number}, address {self.address}, metadata {self.payee_metadata}"
        )

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.strip().title()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Expense(FarmAuditBaseModel):
    """
    The detailed record of outflow.
    Links the 'Who', 'What', and 'Where' of spending.
    Links to the User for accountability and the Payee for audit.
    """

    amount = MoneyField(
        _("Amount Spent"),
        max_digits=14,
        decimal_places=2,
        default_currency="TZS",
        validators=[MinValueValidator(0.01)],
    )

    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, verbose_name=_("Expense Category")
    )
    payee = models.ForeignKey(
        Payee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Paid To"),
    )

    description = models.TextField(_("Details/Notes"), blank=True, null=True)
    payment_method = models.CharField(
        _("Payment Method"),
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        default="CASH",
    )

    # Blueprint for expense_metadata (Receipts/Audit):
    # {
    #   "receipt_image_url": "s3://...",
    #   "vat_amount": 18.0,
    #   "is_reimbursable": false,
    #   "linked_batch_id": "BATCH-2026-001"
    # }
    expense_metadata = models.JSONField(
        _("Expense Audit Data"),
        default=dict,
        blank=True,
        help_text=_("Stores tax details, digital receipts, and batch links."),
    )

    class Meta:
        db_table = "expenses"
        verbose_name = _("Expense")
        verbose_name_plural = _("Expenses")
        ordering = ["-created_on", "-id"]
        indexes = [
            models.Index(fields=["created_by", "created_on"]),
            GinIndex(fields=["expense_metadata"], name="expense_meta_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Expense record "
                f"from: {old_data} to: amount {self.amount}, category {self.category.name}, "
                f"payee {self.payee.name if self.payee else 'N/A'}, method {self.payment_method}"
            )
        return (
            f"Recorded Expense of {self.amount} for category '{self.category.name}' "
            f"paid to {self.payee.name if self.payee else 'N/A'} via {self.payment_method}, "
            f"description: {self.description}, metadata: {self.expense_metadata}"
        )

    def __str__(self):
        return f"{self.created_on.date()} - {self.amount} {self.currency} ({self.category.name})"
