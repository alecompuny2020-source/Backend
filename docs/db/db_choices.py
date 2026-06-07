# lookup_models.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class BaseLookupConfiguration(models.Model):
    """
    Abstract structural base model for all enterprise dynamic configurations.
    Replaces static TextChoices with high-performance real-time relational metadata.
    """
    name = models.CharField(max_length=200, unique=True, verbose_name=_("Name"))
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name=_("Unique Immutable Handle Code"),
        help_text=_("Programmatic slug key used strictly in backend code logic conditions.")
    )
    description = models.TextField(blank=True, verbose_name=_("Operational Description/UI Tooltip"))
    color_hex = models.CharField(max_length=7, default="#7F8C8D", verbose_name=_("Frontend Theme Hex Color"))
    sort_order = models.PositiveSmallIntegerField(default=0, db_index=True, verbose_name=_("Execution Sequencing Order"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active State Configuration Visibility"))

    class Meta:
        abstract = True
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

# --- 1. SYSTEM USER PROFILE & HR CATEGORIES ---
class RegistrationStatus(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Registration Status")
        verbose_name_plural = _("Registration Statuses")

class UserTitle(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("User Title")
        verbose_name_plural = _("User Titles")

class IdentityType(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Identity Type Documentation")
        verbose_name_plural = _("Identity Type Documentations")

class EmploymentType(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Employment Classification Type")
        verbose_name_plural = _("Employment Classification Types")

class AddressType(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Address/Location Type")
        verbose_name_plural = _("Address/Location Types")


# --- 2. LOGISTICS, SHIPPING & INVENTORY CATEGORIES ---
class OrderStatus(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Order Status Definition")
        verbose_name_plural = _("Order Status Definitions")

class ShippingStatus(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Shipping/Logistics Status")
        verbose_name_plural = _("Shipping/Logistics Statuses")

class CarrierType(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Transportation Carrier Type")
        verbose_name_plural = _("Transportation Carrier Types")

class StockMovementType(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Stock Transaction Movement Type")
        verbose_name_plural = _("Stock Transaction Movement Types")

class StorageUnitType(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Storage Unit Infrastructure Placement")
        verbose_name_plural = _("Storage Unit Infrastructure Placements")

class ItemDisposition(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Customer Item Return Disposition")
        verbose_name_plural = _("Customer Item Return Dispositions")

class PackageStatus(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Package Warehouse Inventory Status")
        verbose_name_plural = _("Package Warehouse Inventory Statuses")


# --- 3. FARM PRODUCTION, LIVESTOCK TAXONOMY & HEALTH ---
class SourceChoice(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Resource Procurement Origin Source")
        verbose_name_plural = _("Resource Procurement Origin Sources")

class ProductCategory(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Inventory Product Category")
        verbose_name_plural = _("Inventory Product Categories")

class BirdType(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Avian Bird Classification Type")
        verbose_name_plural = _("Avian Bird Classification Types")

class SpeciesType(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Animal Biological Species Type")
        verbose_name_plural = _("Animal Biological Species Types")

class BreedType(BaseLookupConfiguration):
    # Relational link directly back to the active parent Species type
    species = models.ForeignKey(SpeciesType, on_delete=models.CASCADE, related_name="breeds")
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Animal Genetic Breed Variant")
        verbose_name_plural = _("Animal Genetic Breed Variants")

class FlockBatchStatus(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Flock Batch Production Status")
        verbose_name_plural = _("Flock Batch Production Statuses")

class IncubatorMachineType(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Incubator Machine Configuration Type")
        verbose_name_plural = _("Incubator Machine Configuration Types")

class FarmBlockStatus(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Agricultural Farm Block Rest Status")
        verbose_name_plural = _("Agricultural Farm Block Rest Statuses")

class IncubationCycleStatus(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Incubation Cycle Step Status")
        verbose_name_plural = _("Incubation Cycle Step Statuses")

class StockReadinessStatus(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Stock Market Readiness Status")
        verbose_name_plural = _("Stock Market Readiness Statuses")

class HealthRecordType(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Clinical Health Intervention Record Type")
        verbose_name_plural = _("Clinical Health Intervention Record Types")

class DiseaseOutbreakStatus(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Epidemiological Outbreak Status")
        verbose_name_plural = _("Epidemiological Outbreak Statuses")

class WasteDisposalMethod(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Bio-Waste Management Disposal Method")
        verbose_name_plural = _("Bio-Waste Management Disposal Methods")

class ProductionStatus(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Agronomy Crop Production Status")
        verbose_name_plural = _("Agronomy Crop Production Statuses")

class MeatCutType(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Carcass Commercial Meat Cut Selection")
        verbose_name_plural = _("Carcass Commercial Meat Cut Selections")

class StorageState(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Thermal Preservation Storage State")
        verbose_name_plural = _("Thermal Preservation Storage States")

class FatLevel(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Primal Meat Lipid/Fat Quality Grading Level")
        verbose_name_plural = _("Primal Meat Lipid/Fat Quality Grading Levels")


# --- 4. SALES, FINANCE, BOOKINGS, ASSETS & TASKS ---
class CurrencyCode(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Financial Currency Transaction ISO Code")
        verbose_name_plural = _("Financial Currency Transaction ISO Codes")

class PaymentMethod(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Accounting Payment Channel Settlement Method")
        verbose_name_plural = _("Accounting Payment Channel Settlement Methods")

class SaleInvoiceStatus(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Commercial Sales Invoice Accounting Status")
        verbose_name_plural = _("Commercial Sales Invoice Accounting Statuses")

class CustomerType(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Customer Market Classification Segment")
        verbose_name_plural = _("Customer Market Classification Segments")

class EventBookingStatus(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Hospitality Event Reservation Status")
        verbose_name_plural = _("Hospitality Event Reservation Statuses")

class AssetType(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Fixed Structural Corporate Asset Type")
        verbose_name_plural = _("Fixed Structural Corporate Asset Types")

class RentalUnitType(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Commercial Housing Property Unit Grid Type")
        verbose_name_plural = _("Commercial Housing Property Unit Grid Types")

class UnitOfMeasure(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Inventory Standardized Unit of Measure (UOM)")
        verbose_name_plural = _("Inventory Standardized Units of Measure (UOM)")

class RateType(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Logistics Valuation Service Rate Billing Type")
        verbose_name_plural = _("Logistics Valuation Service Rate Billing Types")

class TicketStatus(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Operational Task/Support Ticket Lifecycle Status")
        verbose_name_plural = _("Operational Task/Support Ticket Lifecycle Statuses")

class TaskPriority(BaseLookupConfiguration):
    class Meta(BaseLookupConfiguration.Meta):
        verbose_name = _("Operational Facility Task Execution Priority")
        verbose_name_plural = _("Operational Facility Task Execution Priorities")
