import secrets
import string
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from common.mixins import BaseEnterpriseModelMixin


class UserAddress(BaseEnterpriseModelMixin):
    """
    Supports multiple addresses per user (e.g., Home, Work, Billing).
    Essential for checkout flow and regional tax/shipping calculations.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses")
    address_type = models.ForeignKey("core.AddressType", on_delete=models.CASCADE, related_name="address_types")
    is_default = models.BooleanField(_("Default Address"), default=False)
    street_address = models.TextField(_("Street Address"))
    city = models.CharField(_("City"), max_length=100)
    state_province = models.CharField(_("State/Province"), max_length=100)
    postal_code = models.CharField(_("Postal Code"), max_length=20)
    country = models.CharField(_("Country"), max_length=100)

    class Meta:
        db_table = "user_address"
        verbose_name = _("User Address")
        verbose_name_plural = _("User Addresses")
        unique_together = ("user", "address_type")

    def get_log_message(self, old_data=None):
        if old_data:
            return f"Updated {self.address_type.title()} Address from: {old_data} to: {self.street_address}, {self.city}"
        return f"Added {self.address_type.title()} Address : {self.street_address}, {self.city}"

    def save(self, *args, **kwargs):
        """Helper: Ensure only one default address exists per type for this user."""
        if self.is_default:
            with transaction.atomic():
                UserAddress.objects.filter(
                    user=self.user, address_type=self.address_type
                ).update(is_default=False)
        super().save(*args, **kwargs)
