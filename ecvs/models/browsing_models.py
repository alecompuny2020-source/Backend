from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.choices import now
from common.mixins import BaseEnterpriseModelMixin

# Create your models here.


class SearchHistory(BaseEnterpriseModelMixin):
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
    created_at = models.DateTimeField(default=now)

    class Meta:
        db_table = "user_search_history"
        ordering = ["-created_at"]
        verbose_name = _("Search History")


class UserInterest(BaseEnterpriseModelMixin):
    """
    Tracks frequency interaction with specific categories (e.g., 'Electronics').
    Used to personalize the homepage 'Inspired by your shopping trends'.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="interests"
    )
    category_name = models.CharField(_("Category/Tag Name"), max_length=100)
    interaction_count = models.PositiveIntegerField(_("Interaction Count"), default=1)
    last_interacted = models.DateTimeField(default=now)

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


class Wishlist(BaseEnterpriseModelMixin):
    """
    Allows users to save products for future purchase.
    Supports multiple named lists.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlists"
    )
    name = models.CharField(_("Wishlist Name"), max_length=255, default="My Wishlist")
    products = models.ManyToManyField(
        "ipss.ProductStock",
        related_name="wishlists",
        blank=True,
    )
    packaged_products = models.ManyToManyField(
        "ipss.PackagedProduct",
        related_name="packaged_wishlists",
        blank=True,
    )
    is_public = models.BooleanField(_("Publicly Visible"), default=False)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField()

    class Meta:
        db_table = "user_wishlist"
        verbose_name = _("Wishlist")

    def get_log_message(self, old_data=None):
        return (
            f"Wishlist '{self.name}' for {self.user} "
            f"updated — public {self.is_public}, products count {self.products.count()}"
        )


class RecentlyViewedItem(BaseEnterpriseModelMixin):
    """Tracks products or specific packages a user has clicked on."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recent_views",
    )
    product = models.ForeignKey(
        "ipss.ProductStock",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="recent_views",
    )
    packaged_product = models.ForeignKey(
        "ipss.PackagedProduct",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="recent_views",
    )

    viewed_at = models.DateTimeField(default=now)

    class Meta:
        db_table = "user_recently_viewed"
        ordering = ["-viewed_at"]

    def clean(self):
        from django.core.exceptions import ValidationError

        if not self.product and not self.packaged_product:
            raise ValidationError(
                "Mstari huu lazima urekodi bidhaa ya kawaida au pakiti maalum."
            )


class Review(BaseEnterpriseModelMixin):
    """Stores customer feedback."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    stock_reference = models.ForeignKey(
        "ipss.ProductStock",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
    )
    packaged_product = models.ForeignKey(
        "ipss.PackagedProduct",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
    )
    sale_item = models.ForeignKey(
        "srs.SaleItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
    )

    comment = models.TextField(_("Comment/Insight"))
    rating = models.IntegerField(_("Rating (1-5)"), null=True, blank=True)
    # Metadata includes: {'verified_purchase': bool, 'helpful_votes': int, 'attachments': list}
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=now)

    class Meta:
        db_table = "product_review"
        ordering = ["-created_at"]
        unique_together = ("user", "sale_item")

    def clean(self):
        from django.core.exceptions import ValidationError

        if not self.stock_reference and not self.packaged_product:
            raise ValidationError(
                "Review lazima ilenge bidhaa ya jumla au pakiti maalum."
            )

    def __str__(self):
        return f"Review by {self.user.username} for {self.stock_reference}"
