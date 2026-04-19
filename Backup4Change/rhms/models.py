from django.db import models
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from phonenumber_field.modelfields import PhoneNumberField

from ..helpers import BOOKING_STATUS, CURRENCY_CHOICES
from ..utils import FarmAuditBaseModel

# Create your models here.

class RecreationZone(FarmAuditBaseModel):
    """
    Specific areas within the FarmLocation (e.g., Kids' Park, Adult Lounge, Garden).
    """

    location = models.ForeignKey(
        settings.FARM_REFERENCE,
        on_delete=models.CASCADE,
        related_name="recreation_zones",
        verbose_name=_("Parent Farm Site"),
    )
    name = models.CharField(_("Zone Name"), max_length=255)
    capacity = models.PositiveIntegerField(
        _("Max Capacity"), help_text=_("Maximum visitors allowed at once for safety.")
    )

    # Blueprint for zone_features:
    # {
    #   "has_wifi": true,
    #   "amenities": ["Swings", "Slides", "Benches", "Barbecue"],
    #   "is_wheelchair_accessible": true,
    #   "security_level": "High"
    # }
    zone_features = models.JSONField(
        _("Zone Features"),
        default=dict,
        blank=True,
        help_text=_("Stores amenities, safety specs, and connectivity details."),
    )
    hourly_rate = MoneyField(
        _("Hourly Rate"), max_digits=14, decimal_places=2, default_currency="TZS"
    )
    # {
    #   "peak_multipliers": {
    #     "Saturday": 1.5,
    #     "Sunday": 1.5,
    #     "PublicHoliday": 2.0
    #   }
    # }
    peak_pricing_config = models.JSONField(
        _("Peak Pricing Configuration"),
        default=dict,
        blank=True,
        help_text=_(
            "JSON mapping of days or holidays to price multipliers. Example: {'Saturday': 1.5, 'Sunday': 1.5, 'PublicHoliday': 2.0}"
        ),
    )
    is_available = models.BooleanField(_("Is Available"), default=True)

    class Meta:
        db_table = "recreation_zone"
        verbose_name = _("Recreation Zone")
        verbose_name_plural = _("Recreation Zones")
        indexes = [
            GinIndex(fields=["zone_features"], name="zone_features_gin_idx"),
        ]

    def get_current_occupancy(self):
        """Calculates how many people are currently checked in."""
        return (
            self.tickets.filter(
                is_used=True, checked_in_at__date=timezone.now().date()
            ).aggregate(total=models.Sum("visitor_count"))["total"]
            or 0
        )

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Recreation Zone '{self.name}' "
                f"from: {old_data} to: capacity {self.capacity}, "
                f"features {self.zone_features}, rate {self.hourly_rate}"
            )
        return (
            f"Created Recreation Zone '{self.name}' at '{self.location.name}' "
            f"with capacity {self.capacity}, hourly rate {self.hourly_rate}, "
            f"features {self.zone_features}"
        )

    # def get_effective_rate(self, target_date=None):
    #     """
    #     Calculates the price for a specific date based on peak multipliers.
    #     Defaults to today if no date is provided.
    #     """
    #     date_to_check = target_date or timezone.now().date()
    #     day_name = date_to_check.strftime('%A')  # e.g., "Saturday"
    #
    #     # Start with the base rate
    #     multiplier = 1.0
    #
    #     # 1. Check for specific day multipliers (Saturday, Sunday, etc.)
    #     day_multipliers = self.peak_pricing_config.get('peak_multipliers', {})
    #     multiplier = day_multipliers.get(day_name, 1.0)
    #
    #     # 2. Logic for Public Holidays (requires a holiday list or integration)
    #     # if is_public_holiday(date_to_check):
    #     #    multiplier = day_multipliers.get('PublicHoliday', multiplier)
    #
    #     return self.hourly_rate * Decimal(str(multiplier))

    def __str__(self):
        return f"{self.name} - {self.location.name}"


class VisitorTicket(FarmAuditBaseModel):
    """
    Tracks day-visitor entry. Essential for real-time revenue and capacity tracking.
    """

    zone = models.ForeignKey(
        RecreationZone, on_delete=models.PROTECT, related_name="tickets"
    )
    ticket_number = models.CharField(
        _("Ticket Serial Number"), max_length=50, unique=True, db_index=True
    )
    visit_date = models.DateField(_("Visit Date"), default=timezone.now)
    visitor_count = models.PositiveIntegerField(_("Number of Visitors"), default=1)

    # Blueprint for ticket_details:
    # {
    #   "package_type": "Family Day Pass",
    #   "includes": ["Swimming", "Farm Tour", "Lunch Voucher"],
    #   "is_group_ticket": true,
    #   "payment_method": "M-Pesa/Cash",
    #   "entry_gate": "North Gate",
    #   "scanned_by": "Agent_ID_45"
    # }
    ticket_details = models.JSONField(
        _("Ticket Metadata"),
        default=dict,
        help_text=_("Stores package inclusions, group details, and payment modes."),
    )
    total_paid = MoneyField(
        _("Total Amount Paid"), max_digits=14, decimal_places=2, default_currency="TZS"
    )
    is_used = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "visitor_ticket"
        verbose_name = _("Visitor Ticket")
        ordering = ["-visit_date"]
        indexes = [
            GinIndex(fields=["ticket_details"], name="ticket_details_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Visitor Ticket '{self.ticket_number}' "
                f"from: {old_data} to: {self.visitor_count} visitors, "
                f"paid {self.total_paid}, used: {self.is_used}"
            )
        if self.is_used and self.checked_in_at:
            return (
                f"Visitor Ticket '{self.ticket_number}' checked in at {self.checked_in_at} "
                f"for {self.visitor_count} visitors in Zone '{self.zone.name}'"
            )
        return (
            f"Issued Visitor Ticket '{self.ticket_number}' "
            f"for {self.visitor_count} visitors in Zone '{self.zone.name}', "
            f"total paid {self.total_paid}"
        )

    def clean(self):
        """Prevent overcrowding."""
        if not self.pk:  # Only check on new ticket issuance
            current_occupancy = self.zone.get_current_occupancy()
            if (current_occupancy + self.visitor_count) > self.zone.capacity:
                raise ValidationError(
                    _(
                        f"Capacity Alert: {self.zone.name} is full. "
                        f"Only {self.zone.capacity - current_occupancy} spots remaining."
                    )
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_number} ({self.visitor_count} pax)"


class FacilityBooking(FarmAuditBaseModel):
    """
    Event Management: Birthdays, Weddings, or Corporate Retreats.
    Links to the Accounting system for deposits and quotes.
    """

    zone = models.ForeignKey(
        RecreationZone, on_delete=models.CASCADE, related_name="bookings"
    )
    customer_name = models.CharField(_("Customer/Org Name"), max_length=255)
    customer_phone = PhoneNumberField(_("Contact Phone"))

    start_time = models.DateTimeField(_("Start Date & Time"))
    end_time = models.DateTimeField(_("End Date & Time"))

    # Blueprint for booking_details:
    # {
    #   "event_type": "Wedding/Birthday",
    #   "catering_required": true,
    #   "setup_notes": "Green Theme with 50 Chairs",
    #   "additional_services": ["PA System", "Decor"]
    # }
    booking_details = models.JSONField(
        _("Booking Details"),
        default=dict,
        blank=True,
        help_text=_("Detailed event setup, catering requirements, and guest lists."),
    )

    total_quote = MoneyField(
        _("Total Quote"), max_digits=14, decimal_places=2, default_currency="TZS"
    )
    deposit_paid = MoneyField(
        _("Deposit Paid"), max_digits=14, decimal_places=2, default_currency="TZS"
    )
    payment_deadline = models.DateTimeField(
        _("Full Payment Deadline"),
        null=True,
        blank=True,
        help_text=_("Date by which the balance must be cleared to avoid cancellation."),
    )

    status = models.CharField(
        _("Status"), max_length=20, choices=BOOKING_STATUS, default="PENDING"
    )

    class Meta:
        db_table = "facility_booking"
        verbose_name = _("Facility Booking")
        indexes = [
            GinIndex(fields=["booking_details"], name="booking_details_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Facility Booking for '{self.customer_name}' "
                f"in Zone '{self.zone.name}' from: {old_data} to: "
                f"status {self.status}, quote {self.total_quote}, deposit {self.deposit_paid}"
            )
        if self.status == "CONFIRMED":
            return (
                f"Facility Booking confirmed for '{self.customer_name}' "
                f"in Zone '{self.zone.name}' from {self.start_time} to {self.end_time}, "
                f"quote {self.total_quote}, deposit {self.deposit_paid}"
            )
        return (
            f"Created Facility Booking for '{self.customer_name}' "
            f"in Zone '{self.zone.name}' from {self.start_time} to {self.end_time}, "
            f"status {self.status}, quote {self.total_quote}, deposit {self.deposit_paid}"
        )

    def clean(self):
        # Ensure end is after start
        if self.end_time <= self.start_time:
            raise ValidationError(_("End time must be after start time."))

        # Check for overlaps in the same zone
        overlap = FacilityBooking.objects.filter(
            zone=self.zone,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
            status__in=["CONFIRMED", "PARTIAL_PAID"],  # Only check active bookings
        ).exclude(pk=self.pk)

        if overlap.exists():
            raise ValidationError(
                _("This zone is already booked for the selected time slot.")
            )

    @property
    def balance_due(self):
        return self.total_quote - self.deposit_paid

    def __str__(self):
        return f"{self.customer_name} - {self.zone.name} ({self.start_time.date()})"


class ZoneClosure(FarmAuditBaseModel):
    """
    Blocks out specific dates for maintenance or private farm use.
    """

    zone = models.ForeignKey(RecreationZone, on_delete=models.CASCADE)
    reason = models.CharField(max_length=255)  # e.g., "Pool Cleaning"
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    class Meta:
        db_table = "recreation_zone_closure"

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Zone Closure for '{self.zone.name}' "
                f"from: {old_data} to: reason '{self.reason}', "
                f"start {self.start_date}, end {self.end_date}"
            )
        return (
            f"Zone Closure created for '{self.zone.name}' "
            f"reason: '{self.reason}', from {self.start_date} to {self.end_date}"
        )
