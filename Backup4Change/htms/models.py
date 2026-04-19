from django.db import models
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from ..helpers import PRIORITY_CHOICES, STATUS_CHOICES, UNIT_TYPES
from ..utils import ActionTrackingBaseModel, FarmAuditBaseModel


# Create your models here.

class Building(FarmAuditBaseModel):
    """
    Represents an apartment block, staff quarters, or a cluster of houses.
    """

    name = models.CharField(_("Building Name"), max_length=255)
    location = models.CharField(_("Location Details"), max_length=255)

    # Blueprint for building_specs:
    # {
    #   "total_units": 10,
    #   "has_electricity": true,
    #   "water_source": "Borehole/City",
    #   "construction_year": 2024,
    #   "insurance_policy": "POL-882"
    # }
    building_specs = models.JSONField(
        _("Building Specifications"),
        default=dict,
        blank=True,
        help_text=_("Stores utility availability, unit counts, and construction data."),
    )

    class Meta:
        db_table = "building"
        verbose_name = _("Building")
        indexes = [
            GinIndex(fields=["building_specs"], name="building_specs_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Building '{self.name}' "
                f"from: {old_data} to: location {self.location}, specs {self.building_specs}"
            )
        return (
            f"Created Building '{self.name}' at location '{self.location}' "
            f"with specs {self.building_specs}"
        )

    def __str__(self):
        return self.name


class RentalUnit(FarmAuditBaseModel):
    """
    A specific room or apartment (Chumba/Nyumba).
    Used for both external tenants and staff benefits.
    """

    building = models.ForeignKey(
        Building, on_delete=models.CASCADE, related_name="units"
    )
    unit_number = models.CharField(_("Unit Number"), max_length=20)
    unit_type = models.CharField(_("Unit Type"), max_length=20, choices=UNIT_TYPES)
    minimum_month_to_pay = models.PositiveIntegerField()

    monthly_rent = MoneyField(
        _("Monthly Rent"), max_digits=14, decimal_places=2, default_currency="TZS"
    )

    # Blueprint for unit_features:
    # {
    #   "size_sq_ft": 200,
    #   "is_furnished": false,
    #   "meter_number": "LUKU-101",
    #   "floor_level": 1
    # }
    unit_features = models.JSONField(
        _("Unit Features"),
        default=dict,
        blank=True,
        help_text=_("Stores square footage, furnishing status, and utility meters."),
    )

    class Meta:
        db_table = "rental_unit"
        verbose_name = _("Rental Unit")
        indexes = [
            GinIndex(fields=["unit_features"], name="unit_features_gin_idx"),
        ]

    @property
    def is_occupied(self):
        """Checks if there is any currently active lease agreement for this unit."""
        return self.leases.filter(is_active=True).exists()

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Rental Unit '{self.unit_number}' in Building '{self.building.name}' "
                f"from: {old_data} to: type {self.unit_type}, rent {self.monthly_rent}, features {self.unit_features}"
            )
        return (
            f"Created Rental Unit '{self.unit_number}' in Building '{self.building.name}' "
            f"type {self.unit_type}, rent {self.monthly_rent}, features {self.unit_features}"
        )

    def __str__(self):
        return f"{self.building.name} - Unit {self.unit_number}"


class Tenant(ActionTrackingBaseModel):
    """
    The Mpangaji. Can be an external citizen or a Farm Employee.
    """

    employee_profile = models.OneToOneField(
        settings.FARM_WORKER,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="housing_tenant",
    )

    # Blueprint for tenant_details:
    # {
    #   "next_of_kin": "John Doe (+255...)",
    #   "employer": "Poultry Farm Ltd",
    #   "occupants_count": 3,
    #   "is_employee_benefit": true
    # }
    tenant_details = models.JSONField(
        _("Tenant Profile Data"),
        default=dict,
        blank=True,
        help_text=_(
            "Stores emergency contacts, occupant counts, and employment status."
        ),
    )
    is_staff = models.BooleanField(
        _("Is Staff Tenant"),
        default=False,
        help_text=_("If True, this tenant is eligible for payroll deductions."),
    )

    is_active = models.BooleanField(_("Is Active Tenant"), default=True)

    class Meta:
        db_table = "tenant"
        verbose_name = _("Tenant")
        indexes = [
            GinIndex(fields=["tenant_details"], name="tenant_details_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Tenant record "
                f"from: {old_data} to: staff {self.is_staff}, active {self.is_active}, details {self.tenant_details}"
            )
        return f"Created Tenant record — staff {self.is_staff}, active {self.is_active}, details {self.tenant_details}"

    # def __str__(self):
    #     if self.is_staff and self.employee_profile:
    #         return f"Staff: {self.employee_profile.get_full_name()}"
    #     return f"External: {self.external_name}"


class LeaseAgreement(models.Model):
    """
    The legal/financial contract.
    Triggers automated Payroll deductions if auto_deduct_payroll is true.
    """

    unit = models.ForeignKey(
        RentalUnit, on_delete=models.PROTECT, related_name="leases"
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name="leases")
    start_date = models.DateField(_("Agreement Start"))
    end_date = models.DateField(_("Agreement End"), null=True, blank=True)
    security_deposit = MoneyField(
        _("Security Deposit"),
        max_digits=14,
        decimal_places=2,
        default=0,
        default_currency="TZS",
        help_text=_("Refundable deposit held against damages or unpaid rent."),
    )
    is_deposit_received = models.BooleanField(_("Deposit Received"), default=False)

    # Blueprint for billing_terms:
    # {
    #   "due_day": 5,
    #   "late_fee_per_day": 1000,
    #   "auto_deduct_payroll": true,
    #   "utility_billing_cycle": "Monthly"
    # }
    billing_terms = models.JSONField(
        _("Billing Terms"),
        default=dict,
        help_text=_("Sets due dates, late fees, and payroll deduction logic."),
    )

    is_active = models.BooleanField(_("Status"), default=True)

    class Meta:
        db_table = "lease_agreement"
        verbose_name = _("Lease Agreement")

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Lease Agreement for Unit '{self.unit.unit_number}' "
                f"from: {old_data} to: tenant {self.tenant.id}, start {self.start_date}, end {self.end_date}, "
                f"deposit {self.security_deposit}, active {self.is_active}"
            )
        return (
            f"Created Lease Agreement for Unit '{self.unit.unit_number}' "
            f"tenant {self.tenant.id}, start {self.start_date}, end {self.end_date}, "
            f"deposit {self.security_deposit}, active {self.is_active}"
        )

    def clean(self):
        # 1. Prevent overlapping leases for the same unit
        if self.is_active:
            overlap = (
                LeaseAgreement.objects.filter(unit=self.unit, is_active=True)
                .exclude(pk=self.pk)
                .exists()
            )
            if overlap:
                raise ValidationError(
                    _("This unit is already occupied by an active lease.")
                )

        # 2. Staff Housing Rules: Only permanent staff (example rule)
        if self.tenant.is_staff and self.tenant.employee_profile:
            if (
                getattr(self.tenant.employee_profile, "employment_type", None)
                == "CASUAL"
            ):
                raise ValidationError(
                    _("Casual workers are not eligible for long-term staff housing.")
                )

    @property
    def total_arrears(self):
        """Calculates the sum of all unpaid invoices for this lease."""
        unpaid = self.invoices.filter(is_paid=False).aggregate(
            total=models.Sum("rent_amount") + models.Sum("utility_charges")
        )
        return unpaid["total"] or 0


class RentInvoice(models.Model):
    """
    Integrates with Accounting for monthly revenue tracking.
    """

    lease = models.ForeignKey(
        LeaseAgreement, on_delete=models.CASCADE, related_name="invoices"
    )
    billing_month = models.DateField(_("Billing Month"))
    rent_amount = MoneyField(
        _("Rent Amount"), max_digits=14, decimal_places=2, default_currency="TZS"
    )
    utility_charges = MoneyField(
        _("Utility Charges"),
        max_digits=14,
        default=0.00,
        decimal_places=2,
        default_currency="TZS",
    )

    # Blueprint for invoice_breakdown:
    # {
    #   "luku_units": 50,
    #   "water_units": 10,
    #   "trash_collection": 5000,
    #   "previous_balance": 0.00
    # }
    invoice_breakdown = models.JSONField(_("Invoice Breakdown"), default=dict)

    is_paid = models.BooleanField(_("Is Paid"), default=False)

    # Linked to Module 13 (Messaging) for M-Pesa/Bank receipts
    payment_metadata = models.JSONField(
        _("Payment Metadata"),
        default=dict,
        blank=True,
        help_text=_("Stores receipt numbers and payment confirmation details."),
    )

    class Meta:
        db_table = "rental_invoice"
        verbose_name = _("Rent Invoice")
        ordering = ["-billing_month"]
        indexes = [
            GinIndex(fields=["payment_metadata"], name="rent_pay_meta_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Rent Invoice for Lease '{self.lease.id}' "
                f"from: {old_data} to: month {self.billing_month}, rent {self.rent_amount}, utilities {self.utility_charges}, paid {self.is_paid}"
            )
        if self.is_paid:
            return (
                f"Rent Invoice for Lease '{self.lease.id}' "
                f"month {self.billing_month} marked as PAID, rent {self.rent_amount}, utilities {self.utility_charges}"
            )
        return (
            f"Created Rent Invoice for Lease '{self.lease.id}' "
            f"month {self.billing_month}, rent {self.rent_amount}, utilities {self.utility_charges}, paid {self.is_paid}"
        )
