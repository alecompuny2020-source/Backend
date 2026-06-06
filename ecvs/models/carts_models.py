from django.db import models
from common.mixins import BaseEnterpriseModelMixin
from django.conf import settings
from common.choices import now
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

# Create your models here.

class ShoppingCart(models.Model):
    """Transient container for items before they become a Sale."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shopping_cart"
    )
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField()

    class Meta:
        db_table = "cart"
        verbose_name = _("Cart")

    def __str__(self):
        return f"Cart for {self.user}"

    def get_log_message(self, old_data=None):
        return (
            f"Shopping Cart for {self.user} "
            f"created at {self.created_at}, last updated {self.updated_at}"
        )



class ShoppingCartItem(models.Model):
    """Individual entries in a cart."""

    cart = models.ForeignKey(
        "ShoppingCart", on_delete=models.CASCADE, related_name="items"
    )
    quantity = models.PositiveIntegerField(default=1)
    product = models.ForeignKey(
        settings.STOCK_PRODUCT_REFERENCE,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="cart_items",
    )
    packaged_product = models.ForeignKey(
        settings.PACKAGED_PRODUCT_REFERENCE,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="cart_items",
    )

    reserved_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "shopping_cart_item"
        unique_together = ("cart", "product")

    def clean(self):
        if not self.product and not self.packaged_product:
            raise ValidationError(
                "Ni lazima uweke bidhaa ya jumla au pakiti maalum kwenye kikapu."
            )

        if self.product and self.packaged_product:
            raise ValidationError(
                "Huwezi kuweka stoki ya jumla na pakiti maalum kwenye mstari mmoja wa kikapu."
            )

        if self.packaged_product and self.quantity > 1:
            raise ValidationError(
                "Pakiti maalum yenye QR Code ya kipekee ina idadi ya 1 tu ghalani. "
                "Kama mteja anataka pakiti nyingine, aongeze mstari mwingine wa pakiti husika."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_still_reserved(self):
        """Check if the 15-minute 'Soft-Lock' on inventory is still active."""
        return timezone.now() < self.reserved_at + timedelta(minutes=15)

    def get_log_message(self, old_data=None):
        return (
            f"Shopping Cart Item added to {self.cart} "
            f"product {self.product}, quantity {self.quantity}, reserved at {self.reserved_at}"
        )
