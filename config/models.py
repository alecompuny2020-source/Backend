from django.db import models
from django.utils.translation import gettext_lazy as _

from common.mixins import BaseLookupConfigurationModelMixin

# Create your models here.


class RegistrationStatus(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "registration_status"
        verbose_name = _("Registration Status")
        verbose_name_plural = _("Registration Statuses")


class UserTitle(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "user_title"
        verbose_name = _("User Title")
        verbose_name_plural = _("User Titles")


class IdentityType(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "Identity_type"
        verbose_name = _("Identity Type Documentation")
        verbose_name_plural = _("Identity Type Documentations")


class EmploymentType(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "employee_type"
        verbose_name = _("Employment Classification Type")
        verbose_name_plural = _("Employment Classification Types")


class AddressType(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "address_type"
        verbose_name = _("Address/Location Type")
        verbose_name_plural = _("Address/Location Types")


class OrderStatus(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "order_status"
        verbose_name = _("Order Status Definition")
        verbose_name_plural = _("Order Status Definitions")


class ShippingStatus(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "shipping_status"
        verbose_name = _("Shipping/Logistics Status")
        verbose_name_plural = _("Shipping/Logistics Statuses")


class CarrierType(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "carrier_type"
        verbose_name = _("Transportation Carrier Type")
        verbose_name_plural = _("Transportation Carrier Types")


class StockMovementType(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "stock_movement_type"
        verbose_name = _("Stock Transaction Movement Type")
        verbose_name_plural = _("Stock Transaction Movement Types")


class StorageUnitType(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "storage_unit_type"
        verbose_name = _("Storage Unit Infrastructure Placement")
        verbose_name_plural = _("Storage Unit Infrastructure Placements")


class ItemDisposition(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "item_disposition"
        verbose_name = _("Customer Item Return Disposition")
        verbose_name_plural = _("Customer Item Return Dispositions")


class PackageStatus(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "package_status"
        verbose_name = _("Package Warehouse Inventory Status")
        verbose_name_plural = _("Package Warehouse Inventory Statuses")


class SourceChoice(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "source_choice"
        verbose_name = _("Resource Procurement Origin Source")
        verbose_name_plural = _("Resource Procurement Origin Sources")


class ProductCategory(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "product_category"
        verbose_name = _("Inventory Product Category")
        verbose_name_plural = _("Inventory Product Categories")


class BirdType(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "bird_type"
        verbose_name = _("Avian Bird Classification Type")
        verbose_name_plural = _("Avian Bird Classification Types")


class SpeciesType(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "species_type"
        verbose_name = _("Animal Biological Species Type")
        verbose_name_plural = _("Animal Biological Species Types")


class BreedType(BaseLookupConfigurationModelMixin):
    species = models.ForeignKey(
        SpeciesType, on_delete=models.CASCADE, related_name="breeds"
    )

    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "breed_type"
        verbose_name = _("Animal Genetic Breed Variant")
        verbose_name_plural = _("Animal Genetic Breed Variants")


class FlockBatchStatus(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "flock_batch_status"
        verbose_name = _("Flock Batch Production Status")
        verbose_name_plural = _("Flock Batch Production Statuses")


class IncubatorMachineType(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "incubator_machine_type"
        verbose_name = _("Incubator Machine Configuration Type")
        verbose_name_plural = _("Incubator Machine Configuration Types")


class FarmBlockStatus(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "farm_block_status"
        verbose_name = _("Agricultural Farm Block Rest Status")
        verbose_name_plural = _("Agricultural Farm Block Rest Statuses")


class IncubationCycleStatus(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "incubation_cycle_status"
        verbose_name = _("Incubation Cycle Step Status")
        verbose_name_plural = _("Incubation Cycle Step Statuses")


class StockReadinessStatus(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "stock_readness_status"
        verbose_name = _("Stock Market Readiness Status")
        verbose_name_plural = _("Stock Market Readiness Statuses")


class HealthRecordType(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "health_record_type"
        verbose_name = _("Clinical Health Intervention Record Type")
        verbose_name_plural = _("Clinical Health Intervention Record Types")


class DiseaseOutbreakStatus(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "disease_outbreak_status"
        verbose_name = _("Epidemiological Outbreak Status")
        verbose_name_plural = _("Epidemiological Outbreak Statuses")


class WasteDisposalMethod(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "waste_disposal_method"
        verbose_name = _("Bio-Waste Management Disposal Method")
        verbose_name_plural = _("Bio-Waste Management Disposal Methods")


class ProductionStatus(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "production_status"
        verbose_name = _("Agronomy Crop Production Status")
        verbose_name_plural = _("Agronomy Crop Production Statuses")


class MeatCutType(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "meat_cut_type"
        verbose_name = _("Carcass Commercial Meat Cut Selection")
        verbose_name_plural = _("Carcass Commercial Meat Cut Selections")


class StorageState(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "storage_state"
        verbose_name = _("Thermal Preservation Storage State")
        verbose_name_plural = _("Thermal Preservation Storage States")


class FatLevel(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "fat_level"
        verbose_name = _("Primal Meat Lipid/Fat Quality Grading Level")
        verbose_name_plural = _("Primal Meat Lipid/Fat Quality Grading Levels")


class CurrencyCode(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "currency_code"
        verbose_name = _("Financial Currency Transaction ISO Code")
        verbose_name_plural = _("Financial Currency Transaction ISO Codes")


class PaymentMethod(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "payment_method"
        verbose_name = _("Accounting Payment Channel Settlement Method")
        verbose_name_plural = _("Accounting Payment Channel Settlement Methods")


class SaleInvoiceStatus(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "sale_invoice_status"
        verbose_name = _("Commercial Sales Invoice Accounting Status")
        verbose_name_plural = _("Commercial Sales Invoice Accounting Statuses")


class CustomerType(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "customer_type"
        verbose_name = _("Customer Market Classification Segment")
        verbose_name_plural = _("Customer Market Classification Segments")


class EventBookingStatus(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "event_booking_status"
        verbose_name = _("Hospitality Event Reservation Status")
        verbose_name_plural = _("Hospitality Event Reservation Statuses")


class AssetType(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "asset_type"
        verbose_name = _("Fixed Structural Corporate Asset Type")
        verbose_name_plural = _("Fixed Structural Corporate Asset Types")


class RentalUnitType(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "rental_unit_type"
        verbose_name = _("Commercial Housing Property Unit Grid Type")
        verbose_name_plural = _("Commercial Housing Property Unit Grid Types")


class UnitOfMeasure(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "unit_of_measure"
        verbose_name = _("Inventory Standardized Unit of Measure (UOM)")
        verbose_name_plural = _("Inventory Standardized Units of Measure (UOM)")


class FarmVehicleType(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "farm_vehicle_type"
        verbose_name = _("Farm Vehicle Type")
        verbose_name_plural = _("Farm Vehicle Types")


class FeedSourceChoices(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "feed_source"
        verbose_name = _("Feed Source")
        verbose_name_plural = _("Feed Sources")


class RateType(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "rate_type"
        verbose_name = _("Logistics Valuation Service Rate Billing Type")
        verbose_name_plural = _("Logistics Valuation Service Rate Billing Types")


class TicketStatus(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "ticket_status"
        verbose_name = _("Operational Task/Support Ticket Lifecycle Status")
        verbose_name_plural = _("Operational Task/Support Ticket Lifecycle Statuses")


class TaskPriority(BaseLookupConfigurationModelMixin):
    class Meta(BaseLookupConfigurationModelMixin.Meta):
        db_table = "task_priority"
        verbose_name = _("Operational Facility Task Execution Priority")
        verbose_name_plural = _("Operational Facility Task Execution Priorities")
