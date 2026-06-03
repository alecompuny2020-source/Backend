from django.db import models
from django.utils.translation import gettext_lazy as _

from common.choices import StorageUnitType
from common.mixins import BaseAddressModelMixin, BaseEnterpriseAuditModelMixin

# Create your models here.


class WarehouseLocation(BaseAddressModelMixin, BaseEnterpriseAuditModelMixin):
    """Physical facilities (e.g., Dodoma Main, Mwanza Staging)."""

    name = models.CharField(_("Location Name"), max_length=100, unique=True)
    code = models.CharField(_("Warehouse Code"), max_length=20, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "warehouse_location"
        verbose_name = _("Warehouse")

    def __str__(self):
        return f"{self.name} ({self.code})"

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Warehouse '{self.name}' "
                f"from: {old_data} to: code {self.code}, address {self.address}"
            )
        return (
            f"Created Warehouse '{self.name}' "
            f"(Code: {self.code}, Address: {self.address})"
        )


class Zone(BaseEnterpriseAuditModelMixin):
    """Sections like 'Cold Storage', 'Electronics', 'Cold Storage' or 'Loading Dock'."""

    warehouse = models.ForeignKey(
        WarehouseLocation, on_delete=models.CASCADE, related_name="zones"
    )
    name = models.CharField(_("Zone Name"), max_length=100)
    code = models.CharField(_("Zone Code"), max_length=10, blank=True)

    class Meta:
        db_table = "warehouse_zone"
        verbose_name = _("Zone")

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Zone '{self.name}' in Warehouse '{self.warehouse.name}' "
                f"from: {old_data} to: code {self.code}"
            )
        return (
            f"Created Zone '{self.name}' in Warehouse '{self.warehouse.name}' "
            f"(Code: {self.code})"
        )

    def __str__(self):
        return f"{self.warehouse.code} - {self.name}"


class StorageUnit(BaseEnterpriseAuditModelMixin):
    """The specific mean: Kabati, Shelf, Clipboard, Drawer, Shelf A1, Freezer 2, or Drawer 10."""

    zone = models.ForeignKey(
        Zone, on_delete=models.CASCADE, related_name="storage_units"
    )
    unit_code = models.CharField(_("Unit Code"), max_length=20)
    unit_type = models.CharField(
        _("Storage Mean"),
        max_length=20,
        choices=StorageUnitType.choices,
        default=StorageUnitType.SHELF,
    )
    max_capacity = models.IntegerField(_("Max Capacity"), default=0)

    class Meta:
        db_table = "storage_unit"
        unique_together = ("zone", "unit_code")
        verbose_name = _("Storage Unit")

    def __str__(self):
        return f"{self.get_unit_type_display()} {self.unit_code}"

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Storage Unit '{self.unit_code}' in Zone '{self.zone.name}' "
                f"from: {old_data} to: type {self.unit_type}, capacity {self.max_capacity}"
            )
        return (
            f"Created Storage Unit '{self.unit_code}' in Zone '{self.zone.name}' "
            f"type {self.unit_type}, capacity {self.max_capacity}"
        )
