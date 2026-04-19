from django.db import models
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from ..helpers import COMMUNICATION_CHOICES, CURRENCY_CHOICES, LANGUAGE_CHOICES


# Create your models here.

class SearchHistory(models.Model):
    """
    Logs user search queries to power 'Recent Searches' and
    provide data for recommendation engines.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="search_history",
    )
    query = models.CharField(_("Search Query"), max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "user_search_history"
        ordering = ["-created_at"]
        verbose_name = _("Search History")


class UserInterest(models.Model):
    """
    Tracks interaction frequency with specific categories (e.g., 'Electronics').
    Used to personalize the homepage like Amazon's 'Inspired by your shopping trends'.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="interests"
    )
    category_name = models.CharField(_("Category/Tag Name"), max_length=100)
    interaction_count = models.PositiveIntegerField(_("Interaction Count"), default=1)
    last_interacted = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "user_interests"
        unique_together = ("user", "category_name")
        verbose_name = _("User Interest")

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated User Interest for {self.user} "
                f"from: {old_data} to: category {self.category_name}, "
                f"interactions {self.interaction_count}, last {self.last_interacted}"
            )
        return (
            f"Created User Interest for {self.user} "
            f"category {self.category_name}, interactions {self.interaction_count}, "
            f"last {self.last_interacted}"
        )


class Wishlist(models.Model):
    """
    Allows users to save products for future purchase.
    Supports multiple named lists.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlists"
    )
    name = models.CharField(_("Wishlist Name"), max_length=255, default="My Wishlist")
    products = models.ManyToManyField(
        settings.STOCK_PRODUCT_REFERENCE, related_name="wishlisted_by"
    )
    is_public = models.BooleanField(_("Publicly Visible"), default=False)

    class Meta:
        db_table = "user_wishlist"
        verbose_name = _("Wishlist")

    def get_log_message(self, old_data=None):
        return (
            f"Wishlist '{self.name}' for {self.user} "
            f"updated — public {self.is_public}, products count {self.products.count()}"
        )


class ShoppingCart(models.Model):
    """Transient container for items before they become a Sale."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shopping_cart"
    )
    created_at = models.DateTimeField(default=timezone.now)
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
        ShoppingCart, on_delete=models.CASCADE, related_name="items"
    )
    quantity = models.PositiveIntegerField(default=1)
    product = models.ForeignKey(
        settings.STOCK_PRODUCT_REFERENCE, on_delete=models.CASCADE
    )
    reserved_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "shopping_cart_item"
        unique_together = ("cart", "product")

    def get_log_message(self, old_data=None):
        return (
            f"Shopping Cart Item added to {self.cart} "
            f"product {self.product}, quantity {self.quantity}, reserved at {self.reserved_at}"
        )

    @property
    def is_still_reserved(self):
        """Check if the 15-minute 'Soft-Lock' on inventory is still active."""
        return timezone.now() < self.reserved_at + timedelta(minutes=15)


class RecentlyViewedItem(models.Model):
    """Tracks products a user has clicked on."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recent_views"
    )
    product = models.ForeignKey(
        settings.STOCK_PRODUCT_REFERENCE, on_delete=models.CASCADE
    )
    viewed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "user_recently_viewed"
        ordering = ["-viewed_at"]


class Review(models.Model):
    """Stores customer feedback."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stock_reference = models.ForeignKey(
        settings.STOCK_PRODUCT_REFERENCE,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
    )
    comment = models.TextField(_("Comment/Insight"))
    rating = models.IntegerField(_("Rating (1-5)"), null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    # Metadata includes: {'verified_purchase': bool, 'helpful_votes': int, 'attachments': list}
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "product_review"
        ordering = ["-created_at"]
        unique_together = ("user", "stock_reference")

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Review for product {self.stock_reference} by {self.user} "
                f"from: {old_data} to: rating {self.rating}, comment '{self.comment}'"
            )
        return (
            f"Created Review for product {self.stock_reference} by {self.user} "
            f"rating {self.rating}, comment '{self.comment}', metadata {self.metadata}"
        )

    def __str__(self):
        return f"Review for {self.stock_reference} by {self.user}"
