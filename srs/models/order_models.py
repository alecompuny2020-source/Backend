from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from phonenumber_field.modelfields import PhoneNumberField

from common.choices import current_time
from common.mixins import BaseEnterpriseAuditModelMixin, BaseEnterpriseModelMixin

# Create your models here.


class Order(BaseEnterpriseAuditModelMixin):
    """
    The financial contract for a sale.
    Links the customer to the revenue and assigns the delivery agent.
    """

    order_number = models.CharField(
        _("Order ID"), max_length=50, unique=True, db_index=True
    )
    offline_customer = models.ForeignKey(
        "srs.Customer",
        on_delete=models.PROTECT,
        related_name="offline_orders",
        null=True,
        blank=True,
    )
    online_customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="onlineline_orders",
        null=True,
        blank=True,
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
    status = models.ForeignKey("config.OrderStatus", on_delete=models.RESTRICT)

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

    def save(self, *args, **kwargs):
        self.total_payable = self.subtotal - self.discount_amount
        super().save(*args, **kwargs)

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

    def get_order_owner(self):
        """Returns string representation of the owner"""

        if self.offline_customer:
            return self.offline_customer.get_full_name()
        if self.online_customer:
            return self.online_customer.get_full_name()
        return _("Unknown Customer")

    def __str__(self):
        return f"Order {self.order_number} - {self.get_order_owner()}"


class OrderItem(BaseEnterpriseModelMixin):
    """
    Snapshot of specific inventory items sold.
    Essential for calculating COGS (Cost of Goods Sold).
    """

    order = models.ForeignKey(Order, related_name="items", on_delete=models.RESTRICT)
    product_stock = models.ForeignKey(
        "ipss.ProductStock", on_delete=models.PROTECT, blank=True
    )
    packaged_product = models.ForeignKey(
        "ipss.PackagedProduct", on_delete=models.PROTECT, blank=True
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
