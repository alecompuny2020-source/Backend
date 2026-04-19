from django.db import models, transaction
from django.conf import settings
import uuid
from django.contrib.postgres.indexes import GinIndex
from django.db.models import Avg
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from helpers.choices import (
    BATCH_STATUS_CHOICES, BIRD_TYPE_CHOICES, CYCLE_STATUS,
    BIRD_TYPE_CHOICES, CURRENCY_CHOICES, HEALTH_RECORD_TYPE, OUTBREAK_STATUS
    )
from utils.mixins import FarmAuditBaseModelMixin
from ppms.models import ProcessingPlant


# Create your models here.


class Farm(FarmAuditBaseModelMixin):
    """ The parent container for every site (e.g., Ihumwa, Nyamhongolo) """

    id = models.UUIDField(primary_key = True, default = uuid.uuid4, editable = False, db_index = True)
    name = models.CharField(_("Farm Name"), max_length=255, unique=True)
    region = models.CharField(_("Region"), max_length=100)
    gps_coordinates = models.CharField(_("GPS Coordinates"), max_length=255, blank=True)

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
        ordering = ['-id']
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



    def get_log_message(self, old_data=None):
        if old_data:
            return f"Updated Farm '{self.name}' in {self.region} from: {old_data} to: {self.site_config}"
        return f"Created new Farm '{self.name}' located in {self.region}"

    def get_farm_details(self):
        return f"{self.name.title()} ({self.region})" if self.name and self.region else f"{self.name}"

    def __str__(self):
        return f"{self.name} ({self.region})"


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
        "hrms.Employee", on_delete=models.CASCADE, related_name="site_tenures"
    )
    start_date = models.DateTimeField(_("Start Date"), default=timezone.now)
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


class FarmShed(FarmAuditBaseModelMixin):
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
            return (timezone.now().date() - self.last_empty_date).days
        return 999  # Assume rested if no date exists

    def get_log_message(self, old_data=None):
        if old_data:
            return f"Updated Shed '{self.name}' at Farm '{self.farm.name}' from: {old_data} to: {self.shed_metadata}"
        return f"Created new Shed '{self.name}' at Farm '{self.farm.name}' with capacity {self.capacity}"

    def __str__(self):
        return f"{self.farm.name} - {self.name}"


class Batch(FarmAuditBaseModelMixin):
    """ A specific flock. Tracks lifecycle from day-old-chicks to depletion."""

    batch_id = models.CharField(
        _("Batch ID"), max_length=50, unique=True, db_index=True
    )
    shed = models.ForeignKey(FarmShed, on_delete=models.PROTECT, related_name="batches")
    bird_type = models.CharField(
        _("Bird Type"), max_length=20, choices=BIRD_TYPE_CHOICES
    )
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
        _("Status"), max_length=20, choices=BATCH_STATUS_CHOICES, default="ACTIVE"
    )

    class Meta:
        db_table = "batch"
        verbose_name = _("Flock Batch")
        verbose_name_plural = _("Flock Batches")
        indexes = [
            GinIndex(fields=["batch_details"], name="batch_details_gin_idx"),
        ]

    @property
    def age_in_days(self) -> int:
        """
        Calculates the current age of the flock.
        Essential for switching from 'Starter' to 'Grower' feed.
        """
        if self.created_on:
            delta = timezone.now() - self.created_on
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

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.full_clean()
        if self.status == "DEPLETED" and self.shed:
            self.shed.last_empty_date = timezone.now().date()
            self.shed.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.batch_id} ({self.bird_type})"


class DailyObservation(FarmAuditBaseModelMixin):
    """ Time-series data for Kiosk monitoring. """

    batch = models.ForeignKey(
        Batch, on_delete=models.CASCADE, related_name="observations"
    )
    mortality_count = models.PositiveIntegerField(_("Mortality"), default=0)
    culls = models.PositiveIntegerField(_("Culls"), default=0)

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


class BreederFlock(FarmAuditBaseModelMixin):
    """
    Parent Stock Management.
    Adds genetic tracking to a standard production batch.
    """

    source_batch = models.OneToOneField(
        Batch,
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
        indexes = [
            GinIndex(fields=["traits"], name="breeder_traits_gin_idx"),
        ]

    @property
    def lifetime_hatchability(self):
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


class Incubator(FarmAuditBaseModelMixin):
    name = models.CharField(max_length=255)
    features = models.JSONField(
        _("Incubator features"),
        default=dict,
        blank=True,
    )
    capacity = models.PositiveIntegerField(
        _("Max Egg Capacity"),
        help_text=_("Total number of eggs this machine can hold."),
    )
    last_sanitized = models.DateTimeField(
        _("Last Sanitization Date"),
        null=True,
        blank=True,
        help_text=_("Tracks bio-security/cleaning dates between cycles."),
    )
    is_active = models.BooleanField(_("Is Active"), default=True)

    class Meta:
        db_table = "incubator"
        verbose_name = _("incubator")
        indexes = [
            GinIndex(fields=["features"], name="incubator_features_gin_idx"),
        ]

    @property
    def current_occupancy(self):
        """Calculates how many eggs are currently inside this machine."""

        # Sum eggs from all active cycles in this incubator
        active_eggs = (
            self.incubation_cycles.filter(
                status="SET",  # Only count cycles currently in progress
                start_date__lte=timezone.now(),
            ).aggregate(total=models.Sum("eggs_set_count"))["total"]
            or 0
        )
        return active_eggs

    @property
    def available_space(self):
        return self.capacity - self.current_occupancy

    def get_availability_date(self):
        """Returns the date when this incubator will be completely empty."""
        last_cycle = (
            self.incubation_cycles.filter(status="SET")
            .order_by("-expected_hatch_date")
            .first()
        )
        return last_cycle.expected_hatch_date if last_cycle else timezone.now()

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Incubator '{self.name}' "
                f"from features: {old_data.get('features')} to: {self.features}, "
                f"capacity: {self.capacity}"
            )
        return (
            f"Registered new Incubator '{self.name}' with capacity {self.capacity} eggs"
        )

    def __str__(self):
        return f"{self.name.title()}"


class IncubationCycle(FarmAuditBaseModelMixin):
    """ Tracks a 'Set' of eggs. Normalizes the 21-day timeline. """

    cycle_id = models.CharField(
        _("Cycle ID"), max_length=50, unique=True, db_index=True
    )
    breeder_flock = models.ForeignKey(
        BreederFlock,
        on_delete=models.PROTECT,
        related_name="incubation_cycles",
        verbose_name=_("Breeder Flock"),
    )
    hatcher = models.ForeignKey(
        Incubator,
        on_delete=models.PROTECT,
        related_name="hatching_cycles",
        verbose_name=_("Incubator Machine"),
    )
    eggs_set_count = models.PositiveIntegerField(_("Total Eggs Set"))
    expected_hatch_date = models.DateTimeField(_("Expected Hatch Date"))

    # Blueprint for incubation_logs (Candling & Transfer):
    # {
    #   "candling_day_07": {"fertile": 480, "infertile": 20, "cracked": 5},
    #   "candling_day_14": {"live_embryo": 470, "dead_in_shell": 10},
    #   "transfer_to_hatcher_count": 465,
    #   "humidity_avg": 55.0,
    #   "temp_avg": 37.5
    # }
    incubation_logs = models.JSONField(
        _("Incubation & Candling Logs"),
        default=dict,
        blank=True,
        help_text=_(
            "Dynamic logs for candling results, machine temps, and embryo health."
        ),
    )
    actual_hatch_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        _("Status"), max_length=20, choices=CYCLE_STATUS, default="SETTING"
    )

    class Meta:
        db_table = "incubation_cycle"
        verbose_name = _("Incubation Cycle")
        ordering = ["-created_on"]
        indexes = [
            GinIndex(fields=["incubation_logs"], name="incubation_log_gin_idx"),
        ]

    @property
    def total_loss(self):
        """
        Calculates eggs that failed to produce a chick.
        Formula: eggs_set_count - total_chicks_hatched
        """
        if hasattr(self, "hatch_record"):
            return self.eggs_set_count - self.hatch_record.total_chicks_hatched
        return None

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Incubation Cycle '{self.cycle_id}' "
                f"status changed from {old_data.get('status')} to {self.status}, "
                f"eggs set: {self.eggs_set_count}"
            )
        if self.status == "HATCHED" and self.actual_hatch_date:
            return (
                f"Incubation Cycle '{self.cycle_id}' completed — "
                f"hatch date {self.actual_hatch_date}, eggs set {self.eggs_set_count}"
            )
        return (
            f"Initiated Incubation Cycle '{self.cycle_id}' "
            f"for Breeder Flock '{self.breeder_flock.breed_line}' "
            f"using Incubator '{self.hatcher.name}' with {self.eggs_set_count} eggs"
        )

    def clean(self):
        # 1. Ensure machine isn't overfilled
        if self.eggs_set_count > self.hatcher.available_space:
            raise ValidationError(
                _(
                    "Not enough space! This incubator only has %(space)s slots available."
                ),
                params={"space": self.hatcher.available_space},
            )

    def __str__(self):
        return f"{self.cycle_id} - {self.get_status_display()}"


class HatchRecord(FarmAuditBaseModelMixin):
    """
    Final quality metrics of the Day-Old-Chicks (DOCs).
    """

    incubation_cycle = models.OneToOneField(
        IncubationCycle,
        on_delete=models.CASCADE,
        related_name="hatch_record",
        verbose_name=_("Incubation Cycle"),
    )
    is_added_to_inventory = models.BooleanField(default=False)
    destination_batch = models.ForeignKey(
        Batch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("The production batch these chicks were moved to."),
    )

    total_chicks_hatched = models.PositiveIntegerField(_("Total Chicks Hatched"))
    grade_a_chicks = models.PositiveIntegerField(_("Grade A Chicks"))
    grade_b_chicks = models.PositiveIntegerField(_("Grade B Chicks"))
    grade_c_chicks = models.PositiveIntegerField(_("Grade C Chicks"))

    # Blueprint for quality_metrics:
    # {
    #   "avg_chick_weight_g": 42.0,
    #   "vaccinations_done": ["Marek's", "IB"],
    #   "cull_count": 3,
    #   "unhatched_eggs_analysis": {"malformation": 2, "external_pipped": 5}
    # }
    quality_metrics = models.JSONField(
        _("Quality Metrics"),
        default=dict,
        help_text=_("Detailed health data, weights, and vaccination records."),
    )

    # Calculated Efficiency
    hatchability_percentage = models.DecimalField(
        _("Hatchability (%)"), max_digits=5, decimal_places=2, editable=False
    )
    cull_weight_total = models.DecimalField(
        _("Total Cull Weight (KG)"),
        max_digits=10,
        decimal_places=3,
        default=0.000,
        help_text=_("Tracks the weight of rejected chicks for waste management."),
    )

    class Meta:
        db_table = "hatch_record"
        verbose_name = _("Hatch Record")
        indexes = [
            GinIndex(fields=["quality_metrics"], name="hatch_quality_gin_idx"),
        ]

    def clean(self):
        if self.total_chicks_hatched > self.incubation_cycle.eggs_set_count:
            raise ValidationError(_("Chicks hatched cannot exceed eggs set."))

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Hatch Record for Cycle '{self.incubation_cycle.cycle_id}' "
                f"from total chicks: {old_data.get('total_chicks_hatched')} "
                f"to: {self.total_chicks_hatched}, "
                f"hatchability: {self.hatchability_percentage:.2f}%"
            )
        if self.is_added_to_inventory and self.destination_batch:
            return (
                f"Hatch Record for Cycle '{self.incubation_cycle.cycle_id}' "
                f"added {self.total_chicks_hatched} chicks to Batch '{self.destination_batch.batch_id}' "
                f"(Grade A: {self.grade_a_chicks}, Grade B: {self.grade_b_chicks}, Grade C: {self.grade_c_chicks})"
            )
        return (
            f"Recorded Hatch for Cycle '{self.incubation_cycle.cycle_id}' — "
            f"Total: {self.total_chicks_hatched}, "
            f"Grade A: {self.grade_a_chicks}, Grade B: {self.grade_b_chicks}, Grade C: {self.grade_c_chicks}, "
            f"Hatchability: {self.hatchability_percentage:.2f}%"
        )

    def save(self, *args, **kwargs):
        # Calculate Hatchability: (Chicks / Eggs Set) * 100
        if self.incubation_cycle.eggs_set_count > 0:
            self.hatchability_percentage = (
                self.total_chicks_hatched / self.incubation_cycle.eggs_set_count
            ) * 100

        with transaction.atomic():
            # Automatically close the cycle when a hatch record is created
            self.incubation_cycle.status = "COMPLETED"
            self.incubation_cycle.actual_hatch_date = timezone.now()
            self.incubation_cycle.save()
            super().save(*args, **kwargs)

    def __str__(self):
        return f"Hatch: {self.incubation_cycle.cycle_id}"



class HealthProtocol(FarmAuditBaseModelMixin):
    """
    Standardized health procedures (e.g., Gumboro Vaccination Protocol).
    Acts as a template for automated reminders in Module 13 (Messaging).
    """

    name = models.CharField(_("Protocol Name"), max_length=255)
    target_bird_type = models.CharField(
        _("Target Bird Type"), max_length=50, choices=BIRD_TYPE_CHOICES
    )

    # Blueprint for protocol_steps (Schedule):
    # [
    #   {"day_age": 1, "task": "Marek's", "type": "VACCINE", "dosage": "0.2ml", "route": "Subcutaneous"},
    #   {"day_age": 7, "task": "Newcastle", "type": "VACCINE", "dosage": "1 drop", "route": "Eye/Nose"}
    # ]
    protocol_steps = models.JSONField(
        _("Protocol Steps"),
        default=list,
        help_text=_("JSON array of scheduled health tasks by bird age (days)."),
    )
    description = models.TextField(_("Detailed Description"), blank=True)

    class Meta:
        db_table = "health_protocol"
        verbose_name = _("Health Protocol")
        verbose_name_plural = _("Health Protocols")
        indexes = [
            GinIndex(fields=["protocol_steps"], name="health_protocol_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Health Protocol '{self.name}' "
                f"for {self.target_bird_type} from: {old_data} to: steps {self.protocol_steps}"
            )
        return (
            f"Created Health Protocol '{self.name}' "
            f"for {self.target_bird_type} with steps {self.protocol_steps}"
        )

    def __str__(self):
        return f"{self.name} ({self.target_bird_type})"


class MedicalRecord(FarmAuditBaseModelMixin):
    """
    Tracks specific health events. Links directly to Accounting for 'Cost per Bird' analysis.
    """

    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name="health_records",
        verbose_name=_("Flock Batch"),
    )
    date_of_administration = models.DateField(_("Date of Administration"), db_index=True, default = timezone.now)
    record_type = models.CharField(
        _("Record Type"), max_length=20, choices=HEALTH_RECORD_TYPE
    )

    # Blueprint for event_details:
    # {
    #   "item_used": "Newcastle Vaccine",
    #   "batch_number": "V882-EXP-2027",
    #   "administration_method": "Drinking Water",
    #   "withdrawal_period_days": 7,
    #   "supplier": "VetPharm Dodoma"
    # }
    event_details = models.JSONField(
        _("Event Details"),
        default=dict,
        help_text=_("Stores item names, batch numbers, and administration methods."),
    )
    cost = MoneyField(
        _("Total Cost"),
        max_digits=14,
        default=0.00,
        decimal_places=2,
        default_currency="TZS",
    )
    notes = models.TextField(_("Clinical Notes"), blank=True)
    withdrawal_end_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "medical_record"
        ordering = ["-date_of_administration"]
        verbose_name = _("Medical Record")
        indexes = [
            GinIndex(fields=["event_details"], name="medical_event_gin_idx"),
        ]

    @property
    def is_in_withdrawal(self):
        """Returns True if the batch is currently under medication restriction."""
        from django.utils.timezone import now

        if self.withdrawal_end_date:
            return self.withdrawal_end_date > now().date()
        return False

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Medical Record for Batch '{self.batch.batch_id}' "
                f"from: {old_data} to: {self.record_type} on {self.date}, "
                f"item: {self.event_details.get('item_used')}, cost: {self.cost}"
            )
        return (
            f"Recorded Medical Event '{self.record_type}' for Batch '{self.batch.batch_id}' "
            f"on {self.date}, item: {self.event_details.get('item_used')}, "
            f"cost: {self.cost}, notes: {self.notes}"
        )

    def save(self, *args, **kwargs):
        days = self.event_details.get("withdrawal_period_days", 0)
        self.withdrawal_end_date = self.date + timedelta(days=days)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.record_type} - {self.batch.batch_id} ({self.date})"


class DiseaseOutbreak(FarmAuditBaseModelMixin):
    """
    Quarantine and Emergency Alerts.
    Triggers 'Module 13' notifications to the Farm Manager and Vet.
    """

    batch = models.ForeignKey(
        Batch,
        on_delete=models.PROTECT,
        verbose_name=_("Impacted Batch"),
    )
    suspected_disease = models.CharField(
        _("Suspected Disease/Condition"), max_length=255
    )
    end_date = models.DateField(_("Resolution Date"), null=True, blank=True)

    # Blueprint for diagnostic_data:
    # {
    #   "symptoms": ["lethargy", "greenish_droppings", "reduced_feed_intake"],
    #   "mortality_at_discovery": 12,
    #   "lab_confirmation_received": true,
    #   "sample_reference": "LAB-DOD-99-A",
    #   "quarantine_measures": "Shed A isolated, footbaths increased"
    # }
    diagnostic_data = models.JSONField(
        _("Diagnostic & Quarantine Data"),
        default=dict,
        help_text=_("Detailed symptoms, lab results, and containment measures."),
    )
    status = models.CharField(
        _("Incident Status"),
        max_length=20,
        choices=OUTBREAK_STATUS,
        default="ACTIVE",
        db_index=True,
    )

    class Meta:
        db_table = "disease_outbreak"
        verbose_name = _("Disease Outbreak")
        ordering = ["-created_on"]
        indexes = [
            GinIndex(fields=["diagnostic_data"], name="outbreak_diag_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Disease Outbreak for Batch '{self.batch.batch_id}' "
                f"from status: {old_data.get('status')} to: {self.status}, "
                f"disease: {self.suspected_disease}"
            )
        if self.status == "RESOLVED" and self.end_date:
            return (
                f"Disease Outbreak '{self.suspected_disease}' for Batch '{self.batch.batch_id}' "
                f"resolved on {self.end_date}"
            )
        return (
            f"Reported Disease Outbreak '{self.suspected_disease}' "
            f"for Batch '{self.batch.batch_id}' (Status: {self.status})"
        )

    def __str__(self):
        return f"Outbreak: {self.suspected_disease} ({self.status})"


class FarmVehicle(FarmAuditBaseModelMixin):
    """
    Tracks trucks, tractors, and delivery bikes.
    Essential for fuel tracking and maintenance scheduling.
    """

    plate_number = models.CharField(_("Plate Number"), max_length=20, unique=True)
    vehicle_type = models.CharField(
        _("Type"), max_length=50
    )  # e.g., Refrigerated Truck, Feed Loader
    max_payload_kg = models.PositiveIntegerField(_("Max Payload (KG)"))

    # Blueprint for vehicle_specs:
    # {
    #   "last_service_km": 15000,
    #   "fuel_type": "Diesel",
    #   "has_gps": true,
    #   "refrigeration_specs": {"min_temp": -20, "max_temp": 4}
    # }
    vehicle_specs = models.JSONField(
        _("Vehicle Specifications"), default=dict, blank=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "farm_vehicle"

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Farm Vehicle '{self.plate_number}' "
                f"from: {old_data} to: "
                f"{{'type': '{self.vehicle_type}', 'payload': {self.max_payload_kg}kg, 'specs': {self.vehicle_specs}}}"
            )
        return (
            f"Registered Farm Vehicle '{self.plate_number}' "
            f"({self.vehicle_type}, Max Payload: {self.max_payload_kg}kg)"
        )


class TransportMovement(FarmAuditBaseModelMixin):
    """ Tracks the journey of assets (Birds, Feed, or Meat). """

    vehicle = models.ForeignKey(FarmVehicle, on_delete=models.PROTECT)
    driver = models.ForeignKey("hrms.Employee", on_delete=models.PROTECT)
    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField(null=True, blank=True)

    # Blueprint for transit_data:
    # {
    #   "cargo_type": "LIVE_CHICKS",
    #   "item_count": 5000,
    #   "disinfection_done": true,
    #   "temp_at_arrival": 22.5,
    #   "mortality_during_transit": 2
    # }
    transit_data = models.JSONField(_("Transit Audit Data"), default=dict)

    class Meta:
        db_table = "transport_movement"

    @property
    def distance_covered(self):
        if self.end_odometer and self.start_odometer:
            return self.end_odometer - self.start_odometer
        return 0

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Transport Movement for Vehicle '{self.vehicle.plate_number}' "
                f"from: {old_data} to: origin {self.origin}, destination {self.destination}, "
                f"cargo {self.transit_data.get('cargo_type')}, count {self.transit_data.get('item_count')}"
            )
        if self.arrival_time:
            return (
                f"Transport Movement completed for Vehicle '{self.vehicle.plate_number}' "
                f"from {self.origin} to {self.destination}, cargo {self.transit_data.get('cargo_type')}, "
                f"count {self.transit_data.get('item_count')}, arrived at {self.arrival_time}"
            )
        return (
            f"Transport Movement initiated for Vehicle '{self.vehicle.plate_number}' "
            f"from {self.origin} to {self.destination}, cargo {self.transit_data.get('cargo_type')}, "
            f"count {self.transit_data.get('item_count')}, departed at {self.departure_time}"
        )

    def clean(self):
        """ Ensure cargo doesn't exceed vehicle capacity."""
        cargo_weight = self.transit_data.get("total_weight_kg", 0)
        if cargo_weight > self.vehicle.max_payload_kg:
            raise ValidationError(
                _(
                    f"Overload Alert: Cargo weight ({cargo_weight}kg) "
                    f"exceeds vehicle capacity ({self.vehicle.max_payload_kg}kg)."
                )
            )

        if self.arrival_time and self.arrival_time < self.departure_time:
            raise ValidationError(_("Arrival time cannot be before departure time."))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.vehicle.plate_number}: {self.origin} -> {self.destination}"
