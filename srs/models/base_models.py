from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from phonenumber_field.modelfields import PhoneNumberField

from common.choices import current_time
from common.mixins import BaseEnterpriseAuditModelMixin

# Create your models here.


class Promotion(BaseEnterpriseAuditModelMixin):
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

    @property
    def is_active(self):
        return self.valid_from <= current_time <= self.valid_to

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


class Customer(BaseEnterpriseAuditModelMixin):
    """
    Manages RETAIL, WHOLESALE (Hotels), and DISTRIBUTOR entities.
    Central to the CRM and Account Receivables.
    """

    name = models.CharField(_("Customer Name"), max_length=255)
    status = models.ForeignKey("core.CustomerType", on_delete=models.RESTRICT)
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
