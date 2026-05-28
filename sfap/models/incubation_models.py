from django.db import models, transaction
from common.mixins import BaseEnterpriseAuditModelMixin
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.indexes import GinIndex
from common.choices import IncubatorMachineType, IncubationCycleStatus, current_time


class Incubator(BaseEnterpriseAuditModelMixin):
    name = models.CharField(max_length=255)
    machine_type = models.CharField(
        max_length=20,
        choices=IncubatorMachineType,
        default=IncubatorMachineType.COMBINED
    )
    farm = models.ForeignKey(
        "sfap.Farm",
        on_delete=models.CASCADE,
        related_name="incubators",
        verbose_name=_("Location/Farm")
    )
    code = models.CharField(
        _("Machine Code or Machine Identification (Short code like 'INC-01')"),
        max_length=20,
        unique=True,
        db_index=True
    )
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
        verbose_name = _("Incubator")
        verbose_name_plural = _("Incubators")
        indexes = [
            GinIndex(fields=["features"], name="incubator_features_gin_idx"),
        ]

    @property
    def current_occupancy(self) -> int:
        """Calculates how many eggs are currently inside this machine."""

        # Sum eggs from all active cycles in this incubator
        active_eggs = (
            self.incubation_cycles.filter(
                status="SET",  # Only count cycles currently in progress
                start_date__lte=current_time,
            ).aggregate(total=models.Sum("eggs_set_count"))["total"]
            or 0
        )
        return active_eggs

    @property
    def available_space(self) -> int:
        return max(0, self.capacity - self.current_occupancy)

    @property
    def availability_date(self) -> str:
        """Returns the date when this incubator will be completely empty."""
        last_cycle = (
            self.incubation_cycles.filter(status="SET")
            .order_by("-expected_hatch_date")
            .first()
        )
        return last_cycle.expected_hatch_date if last_cycle else current_time

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



class IncubationCycle(BaseEnterpriseAuditModelMixin):
    """ Tracks a 'Set' of eggs. Normalizes the 21-day timeline.
        Identity Format: [SITE]-[TYPE]-CYC-[YYYYMMDD]-[SEQ]
    """

    cycle_number = models.CharField(
        _("Cycle Number"), max_length=50, unique=True, db_index=True
    )
    breeder_flock = models.ForeignKey(
        'sfap.BreederFlock',
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
    # cost_per_egg = models.DecimalField(
    #     _("Cost Per Egg"),
    #     max_digits=10,
    #     decimal_places=2,
    #     help_text=_("The cost price of a single egg at the time of setting.")
    # )
    #
    # additional_costs = models.DecimalField(
    #     _("Additional Costs"),
    #     max_digits=10,
    #     decimal_places=2,
    #     default=Decimal("0.00"),
    #     help_text=_("Extra costs like specific vaccines or specialized labor for this cycle.")
    # )
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
        _("Status"), max_length=20, choices=IncubationCycleStatus, default=IncubationCycleStatus.SETTING
    )

    class Meta:
        db_table = "incubation_cycle"
        verbose_name = _("Incubation Cycle")
        ordering = ["-created_on"]
        indexes = [
            GinIndex(fields=["incubation_logs"], name="incubation_log_gin_idx"),
        ]

    @property
    def total_loss(self) -> int:
        """
        Calculates eggs that failed to produce a chick.
        Formula: eggs_set_count - total_chicks_hatched
        """
        if hasattr(self, "hatch_record"):
            return self.eggs_set_count - self.hatch_record.total_chicks_hatched
        return None

    # @property
    # def total_initial_investment(self):
    #     """
    #     Total value of the eggs plus additional costs.
    #     """
    #     return (self.eggs_set_count * self.cost_per_egg) + self.additional_costs
    #
    # @property
    # def projected_chick_cost(self):
    #     """
    #     Calculates expected cost per chick based on standard hatch rate (e.g., 85%).
    #     """
    #     expected_hatch_rate = Decimal("0.85")
    #     expected_chicks = self.eggs_set_count * expected_hatch_rate
    #     if expected_chicks > 0:
    #         return self.total_initial_investment / expected_chicks
    #     return Decimal("0.00")

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Incubation Cycle '{self.cycle_number}' "
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

    def _generate_cycle_number(self):
        """
        Constructs cycle number: [SITE]-[TYPE]-CYC-[YYYYMMDD]-[SEQ]
        Example: HOM-BRO-CYC-20260517-0001
        """
        farm = self.hatcher.farm
        site_code = getattr(farm, 'code', farm.name[:3]).upper()

        bird_type = getattr(self.breeder_flock, 'bird_type', 'GEN')
        type_code = bird_type[:3].upper()

        date_str = current_time.strftime('%Y%m%d')

        prefix = f"{site_code}-{type_code}-CYC-{date_str}-"

        last_cycle = IncubationCycle.objects.filter(
            cycle_id__startswith=prefix
        ).order_by('-cycle_id').first()

        if not last_cycle:
            new_seq = "0001"
        else:
            try:
                # Extract the number from the end (e.g., ...-0001 -> 1)
                last_number_str = last_cycle.cycle_number.split('-')[-1]
                new_seq = f"{int(last_number_str) + 1:04d}"
            except (ValueError, IndexError):
                new_seq = "0001"

        return f"{prefix}{new_seq}"

    def clean(self):
        # 1. Ensure machine isn't overfilled
        if self.eggs_set_count > self.hatcher.available_space:
            raise ValidationError(
                _(
                    "Not enough space! This incubator only has %(space)s slots available."
                ),
                params={"space": self.hatcher.available_space},
            )

    @transaction.atomic
    def save(self, *args, **kwargs):
        # if not self.cost_per_egg and self.breeder_flock:
        #     # Assuming BreederFlock has an egg_unit_price field
        #     self.cost_per_egg = getattr(self.breeder_flock, 'egg_unit_price', Decimal("0.00"))
        #
        # Auto-generate Cycle ID for new records
        if not self.cycle_number:
            self.cycle_number = self._generate_cycle_number()

        # Run validations (Capacity check)
        self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cycle_number} - {self.get_status_display()}"



class HatchRecord(BaseEnterpriseAuditModelMixin):
    """ Final quality metrics of the Day-Old-Chicks (DOCs). """

    incubation_cycle = models.OneToOneField(
        IncubationCycle,
        on_delete=models.CASCADE,
        related_name="hatch_record",
        verbose_name=_("Incubation Cycle"),
    )
    is_added_to_inventory = models.BooleanField(default=False)
    destination_batch = models.ForeignKey(
        'sfap.Batch',
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
        verbose_name_plural = _("Hatch Records")
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
