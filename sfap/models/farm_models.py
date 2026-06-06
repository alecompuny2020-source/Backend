from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Avg
from django.utils.translation import gettext_lazy as _

from common.choices import (
    BirdType,
    FarmBlockStatus,
    FlockBatchStatus,
    current_time,
    now,
    SpeciesType,
    BreedType
)
from common.mixins import BaseAddressModelMixin, BaseEnterpriseAuditModelMixin
from ppms.models import ProcessingPlant

# Create your models here.


class Farm(BaseAddressModelMixin, BaseEnterpriseAuditModelMixin):
    """The parent container for every farm or site (e.g., Ihumwa, Nyamhongolo, Nyamori and etc)"""

    name = models.CharField(_("Farm Name"), max_length=255, unique=True)
    manager = models.ForeignKey(
        "hrms.Employee",
        on_delete=models.SET_NULL,
        null=True,
        related_name="managed_sites",
        verbose_name=_("Farm Manager"),
    )

    # Blueprint for site_config:
    # {
    #   "power_source": "Solar/Grid",
    #   "water_source": "Borehole",
    #   "total_acreage": 50.0,
    #   "currency_context": "TZS",
    #   "contact_number": "+255..."
    # }
    site_config = models.JSONField(
        _("Site Configuration"),
        default=dict,
        blank=True,
        help_text=_("Stores utility types, acreage, and regional site settings."),
    )
    is_quarantined = models.BooleanField(
        _("Quarantine Status"),
        default=False,
        help_text=_(
            "If True, all batch movements and processing sessions are blocked for bio-security."
        ),
    )
    is_active = models.BooleanField(_("Is Active"), default=True)

    class Meta:
        db_table = "farm"
        verbose_name = _("Farm")
        verbose_name_plural = _("Farms")
        ordering = ["name"]
        indexes = [
            GinIndex(fields=["site_config"], name="farm_site_cfg_gin_idx"),
        ]
        # permissions = [
        #     ("add_daily_observation", "Can add daily observation"),
        #     ("log_mortality", "Can log mortality"),
        #     ("update_water_intake", "Can update water intake"),
        #     ("log_egg_collection", "Can log egg collection"),
        #     ("approve_batch_movement", "Can approve batch movement"),
        #     ("view_kpi_dashboard", "Can view KPI dashboard"),
        #     ("assign_shed_worker", "Can assign shed worker"),
        #     ("manage_biosecurity_lockdown", "Can manage biosecurity lockdown"),
        #     ("manage_incubation_cycle", "Can manage incubation cycle"),
        #     ("log_hatch_results", "Can log hatch results"),
        #     ("update_breeder_traits", "Can update breeder traits"),
        #     ("check_egg_fertility", "Can check egg fertility"),
        #     ("prescribe_medication", "Can prescribe medication"),
        #     ("log_vaccination", "Can log vaccination"),
        #     ("declare_disease_outbreak", "Can declare disease outbreak"),
        #     ("issue_health_clearance", "Can issue health clearance"),
        # ]

    @property
    def full_address(self) -> str:
        """Helper to extract the JSON metadata for display."""
        street = self.address_metadata.get("street_name", "N/A")
        return f"{street}, {self.ward}, {self.district}, {self.region}"

    def get_log_message(self, old_data=None):
        if old_data:
            return f"Updated Farm '{self.name}' in {self.region} from: {old_data} to: {self.site_config}"
        return f"Created new Farm '{self.name}' located in {self.region}"

    def get_farm_details(self) -> str:
        return (
            f"{self.name.title()} ({self.region})"
            if self.name and self.region
            else f"{self.name}"
        )

    def __str__(self):
        return f"{self.name} - {self.region}"


class ManagerHistory(models.Model):
    """
    Tracks the lifecycle of who managed which site.
    Essential for accountability in the Accounting/Audit modules.
    """

    farm = models.ForeignKey(
        Farm, on_delete=models.PROTECT, related_name="management_history"
    )
    plant = models.ForeignKey(
        ProcessingPlant,
        on_delete=models.PROTECT,
        related_name="Plant_management_history",
        null=True,
        blank=True,
    )
    manager = models.ForeignKey(
        "hrms.Employee", on_delete=models.PROTECT, related_name="site_tenures"
    )
    start_date = models.DateTimeField(_("Start Date"), default=now)
    end_date = models.DateTimeField(_("End Date"), null=True, blank=True)

    # Blueprint for tenure_metadata:
    # {
    #   "handover_notes": "All stocks verified",
    #   "previous_performance_rating": 4.5,
    #   "reason_for_exit": "Transfer to Nyamhongolo"
    # }
    tenure_metadata = models.JSONField(_("Tenure Metadata"), default=dict, blank=True)
    is_current = models.BooleanField(_("Current Manager"), default=True)

    class Meta:
        db_table = "audit_manager_lifecycle"
        verbose_name = _("Manager History")
        ordering = ["-start_date"]
        indexes = [
            GinIndex(fields=["tenure_metadata"], name="mgr_history_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Manager History for Farm '{self.farm.name}' "
                f"from manager: {old_data.get('manager')} to: {self.manager}"
            )
        if self.end_date:
            return f"Manager {self.manager} tenure at Farm '{self.farm.name}' ended on {self.end_date}"
        return f"Manager {self.manager} assigned to Farm '{self.farm.name}' starting {self.start_date}"

    def __str__(self):
        return self.farm.name.title()


class FarmShed(BaseEnterpriseAuditModelMixin):
    """Represents physical housing. Links birds to a specific structure."""

    name = models.CharField(_("Shed Name"), max_length=100)
    farm = models.ForeignKey(Farm, on_delete=models.RESTRICT, related_name="sheds")
    capacity = models.PositiveIntegerField(_("Max Capacity (Birds)"))

    # Blueprint for shed_metadata:
    # {
    #   "ventilation": "Automated",
    #   "feeder_type": "Automatic",
    #   "floor_type": "Deep Litter",
    #   "sq_ft": 2500
    # }
    shed_metadata = models.JSONField(_("Shed Specifications"), default=dict, blank=True)
    last_empty_date = models.DateField(
        _("Last Date Empty"),
        null=True,
        blank=True,
        help_text=_(
            "Date the previous batch was cleared. Used to ensure a 14-day bio-security break."
        ),
    )
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        db_table = "shed"
        unique_together = ("farm", "name")
        verbose_name = _("Farm Shed")
        indexes = [
            GinIndex(fields=["shed_metadata"], name="shed_spec_gin_idx"),
        ]

    @property
    def rest_days(self) -> int:
        """Calculates how many days the shed has been resting."""
        if self.last_empty_date:
            return (current_time.date() - self.last_empty_date).days
        return 999  # Assume rested if no date exists

    def get_log_message(self, old_data=None):
        if old_data:
            return f"Updated Shed '{self.name}' at Farm '{self.farm.name}' from: {old_data} to: {self.shed_metadata}"
        return f"Created new Shed '{self.name}' at Farm '{self.farm.name}' with capacity {self.capacity}"

    def __str__(self):
        return f"{self.farm.name} - {self.name}"


class FarmBlock(BaseEnterpriseAuditModelMixin):
    """
    Vitalu vya Kilimo Ikolojia ndani ya Shamba.
    Hivi hutumika kwa mzunguko wa wanyama (Rotational Grazing).
    """

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="blocks")
    name = models.CharField(max_length=100)
    size_acres = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(
        _("Hali ya Kitalu"),
        max_length=20,
        choices=FarmBlockStatus,
        default=FarmBlockStatus.RESTING,
        help_text=_("Inatusaidia kuratibu mzunguko wa ikolojia kati ya kuku na mazao."),
    )
    current_crops = ArrayField(
        models.CharField(max_length=100, blank=True),
        blank=True,
        default=list,
        help_text="Orodha ya mazao yaliyopo sasa kwenye hili eneo (Kilimo mseto)",
    )

    # Data ya IoT
    soil_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.farm.name} - {self.name}"


class Batch(BaseEnterpriseAuditModelMixin):
    """A specific flock. Tracks lifecycle from day-old-chicks to depletion."""

    batch_id = models.CharField(
        _("Batch ID"), max_length=50, unique=True, db_index=True
    )
    shed = models.ForeignKey(FarmShed, on_delete=models.PROTECT, related_name="batches")
    current_block = models.ForeignKey(
        FarmBlock, on_delete=models.SET_NULL, null=True, blank=True
    )
    bird_type = models.CharField(_("Bird Type"), max_length=20, choices=BirdType)
    species = models.CharField(max_length=20, choices=SpeciesType.choices)
    breed = models.CharField(max_length=30, choices=BreedType.choices)
    initial_count = models.PositiveIntegerField(_("Initial Bird Count"))
    current_count = models.PositiveIntegerField(_("Current Bird Count"))
    expected_depletion_date = models.DateField(
        _("Expected Depletion"), null=True, blank=True
    )

    # Blueprint for batch_details:
    # {
    #   "hatchery_source": "Interchick",
    #   "breed": "Ross 308",
    #   "cost_per_chick": 1500.00,
    #   "currency": "TZS",
    #   "initial_weight_avg": 0.45
    # }
    batch_details = models.JSONField(_("Batch Details"), default=dict, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=FlockBatchStatus,
        default=FlockBatchStatus.ACTIVE,
    )

    class Meta:
        db_table = "batch"
        verbose_name = _("Flock Batch")
        verbose_name_plural = _("Flock Batches")
        indexes = [
            GinIndex(fields=["batch_details"], name="batch_details_gin_idx"),
        ]

    def clean(self):
        # 1. Capacity Check
        if self.initial_count > self.shed.capacity:
            raise ValidationError(
                _(f"Shed capacity exceeded! Max: {self.shed.capacity}")
            )

        # 2. Bio-Security Check (Rest Period)
        if not self.pk and self.shed.rest_days < 14:
            raise ValidationError(
                _(
                    f"Biosecurity Risk: Shed has only rested for {self.shed.rest_days} days. "
                    "Minimum 14 days required."
                )
            )

    def _generate_batch_number(self):
        """
        Constructs batch number: [SITE]-[TYPE]-[YYYYMMDD]-[SEQ]
        Example: HOM-LOC-20260517-0001
        """

        farm = self.shed.farm
        site_code = getattr(farm, "code", farm.name[:3]).upper()

        type_code = self.bird_type[:3].upper()
        date_str = current_time().strftime("%Y%m%d")
        prefix = f"{site_code}-{type_code}-{date_str}-"

        last_batch = (
            Batch.objects.filter(batch_id__startswith=prefix)
            .order_by("-batch_id")
            .first()
        )

        if not last_batch:
            new_seq = "0001"
        else:
            try:
                # Extract the number from the end of the string
                last_number_str = last_batch.batch_id.split("-")[-1]
                new_seq = f"{int(last_number_str) + 1:04d}"
            except (ValueError, IndexError):
                new_seq = "0001"

        return f"{prefix}{new_seq}"

    @transaction.atomic
    def save(self, *args, **kwargs):
        # Only generate ID for new records
        if not self.batch_id:
            self.batch_id = self._generate_batch_id()

        self.full_clean()
        if self.status == "DEPLETED" and self.shed:
            self.shed.last_empty_date = current_time.date()
            self.shed.save()
        super().save(*args, **kwargs)

    @property
    def age_in_days(self) -> int:
        """
        Calculates the current age of the flock.
        Essential for switching from 'Starter' to 'Grower' feed.
        """
        if self.created_on:
            delta = current_time - self.created_on
            return delta.days
        return 0

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Batch '{self.batch_id}' ({self.bird_type}) "
                f"from status: {old_data.get('status')} to: {self.status}, "
                f"current count: {self.current_count}"
            )
        if self.status == "DEPLETED":
            return f"Batch '{self.batch_id}' ({self.bird_type}) marked as DEPLETED in Shed '{self.shed.name}'"
        return f"Initiated Batch '{self.batch_id}' ({self.bird_type}) with {self.initial_count} birds in Shed '{self.shed.name}'"

    def __str__(self):
        return f"{self.batch_id} ({self.bird_type})"


class DailyObservation(BaseEnterpriseAuditModelMixin):
    """Time-series data for Kiosk or farm monitoring."""

    batch = models.ForeignKey(
        Batch, on_delete=models.CASCADE, related_name="observations"
    )
    mortality_count = models.PositiveIntegerField(_("Mortality"), default=0)
    culls = models.PositiveIntegerField(_("Culls"), default=0)
    eggs_collected = models.IntegerField(_("Eggs Collected"), default=0)
    manure_volume_kg = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)

    # Blueprint for environmental_data:
    # {
    #   "temp_min": 28, "temp_max": 34,
    #   "water_consumed": 450,
    #   "feed_consumed_kg": 120.5,
    #   "temp_min_c": 28.5,
    #   "temp_max_c": 32.0,
    #   "humidity_pct": 65,
    #   "water_liters": 450,
    #   "lighting_hours": 16,
    #   "litter_condition": "Dry",
    #   "vaccination_given": "Gumboro"
    # }
    environmental_data = models.JSONField(
        _("Environmental & Feeding Data"), default=dict
    )

    class Meta:
        db_table = "daily_observation"
        verbose_name = _("Flock Observation")
        verbose_name_plural = _("Flock Observations")
        unique_together = ("batch", "created_on")
        indexes = [
            GinIndex(fields=["environmental_data"], name="daily_env_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        return (
            f"Recorded Daily Observation for Batch '{self.batch.batch_id}' "
            f"mortality: {self.mortality_count}, culls: {self.culls}, "
            f"environmental data: {self.environmental_data}"
        )

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Update Batch current_count on every observation."""
        is_new = self._state.adding
        if is_new:
            total_loss = self.mortality_count + self.culls
            if total_loss > 0:
                self.batch.current_count -= total_loss
                if self.batch.current_count < 0:
                    raise ValidationError(
                        _("Mortality cannot exceed current bird count.")
                    )
                self.batch.save()

        super().save(*args, **kwargs)


class BreederFlock(BaseEnterpriseAuditModelMixin):
    """
    Parent Stock Management.
    Adds genetic tracking to a standard production batch.
    """

    source_batch = models.OneToOneField(
        "sfap.Batch",
        on_delete=models.CASCADE,
        related_name="breeder_details",
        verbose_name=_("Source Batch"),
    )
    breed_line = models.CharField(_("Breed Line"), max_length=100)
    genetic_source = models.CharField(_("Genetic Origin"), max_length=255)

    # Blueprint for traits:
    # {
    #   "avg_egg_weight_g": 60.5,
    #   "fertility_rate_target": 92.0,
    #   "peak_lay_age_weeks": 28,
    #   "expected_doc_yield": 0.85
    # }
    traits = models.JSONField(
        _("Genetic Traits"),
        default=dict,
        blank=True,
        help_text=_("Stores phenotypic and performance targets for this breed line."),
    )

    class Meta:
        db_table = "breeder_flock"
        verbose_name = _("Breeder Flock")
        verbose_name_plural = _("Breeder Flocks")
        indexes = [
            GinIndex(fields=["traits"], name="breeder_traits_gin_idx"),
        ]

    @property
    def lifetime_hatchability(self) -> int:
        """Calculates the average hatchability across all cycles for this flock."""
        return (
            self.incubation_cycles.filter(hatch_record__isnull=False).aggregate(
                avg_hatch=Avg("hatch_record__hatchability_percentage")
            )["avg_hatch"]
            or 0
        )

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Breeder Flock '{self.breed_line}' "
                f"from traits: {old_data.get('traits')} to: {self.traits}"
            )
        return (
            f"Created Breeder Flock '{self.breed_line}' "
            f"linked to Batch '{self.source_batch.batch_id}' "
            f"with genetic source '{self.genetic_source}'"
        )

    def __str__(self):
        return f"{self.breed_line} ({self.source_batch.batch_id})"
