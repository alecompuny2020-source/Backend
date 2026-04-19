from django.db import models
from django.utils.translation import gettext_lazy as _
from utils.audit_track import FarmAuditBaseModel

# Create your models here.

class Supplier(FarmAuditBaseModel):
    """Poultry keepers who supply stock."""
    name = models.CharField(_("Supplier Name"), max_length=100)
    contact = models.CharField(_("Contact Info"), max_length=100, blank=True)
    location = models.CharField(_("Farm Location"), max_length=150, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "supplier"
        verbose_name = _("Supplier")
        verbose_name_plural = _("Suppliers")

    def __str__(self):
        return self.name


# class Client(models.Model):
#     """Market buyers (wholesalers, retailers)."""
#     name = models.CharField(_("Client Name"), max_length=100)
#     contact = models.CharField(_("Contact Info"), max_length=100, blank=True)
#     location = models.CharField(_("Client Location"), max_length=150, blank=True)
#     client_type = models.CharField(
#         _("Type"), max_length=50,
#         choices=[("WHOLESALER", "Wholesaler"), ("RETAILER", "Retailer")],
#         default="RETAILER"
#     )
#
#     def __str__(self):
#         return f"{self.name} ({self.client_type})"


# class Procurement(FarmAuditBaseModel):
#     """Records buying from poultry keepers."""
#     supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
#     product = models.ForeignKey('ipss.Product', on_delete=models.PROTECT)
#     quantity_bought = models.PositiveIntegerField()
#     price_per_unit = models.DecimalField(max_digits=12, decimal_places=2) # TZS
#     transport_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
#     date_purchased = models.DateField(default=timezone.now)
#
#     @property
#     def landed_cost_per_unit(self):
#         """Total cost including transport divided by quantity."""
#         return (self.price_per_unit * self.quantity_bought + self.transport_cost) / self.quantity_bought


# Formula: $\frac{(Quantity \times Unit Price) + Transport}{Quantity}$
