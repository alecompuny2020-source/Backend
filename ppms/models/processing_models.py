from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _

from common.mixins import BaseEnterpriseAuditModelMixin

# Create your models here.


class ProcessingPlant(BaseEnterpriseAuditModelMixin):
    """Represents the physical facility or station where processing occurs."""

    name = models.CharField(_("Plant Name"), max_length=100, unique=True)
    location = models.CharField(_("Location Details"), max_length=255)
    # farm = models.ForeignKey(
    #     'sfap.Farm',
    #     on_delete=models.RESTRICT,
    #     related_name="locations",
    #     verbose_name=_("Farm to which a plant is"),
    # )
    plant_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="managed_plants",
        verbose_name=_("Plant Manager"),
    )

    # Blueprint for plant_config:
    # {
    #   "cold_room_temp": -18,
    #   "daily_capacity": 5000,
    #   "health_certs": ["TFDA_2024", "HALAL_MAIN"]
    # }
    plant_config = models.JSONField(_("Plant Configuration"), default=dict, blank=True)

    # Blueprint for certification_info:
    # {
    #   "halal_certified": true,
    #   "health_permit_no": "EXP-2027-DOD",
    #   "iso_9001": true,
    #   "last_inspection_date": "2026-01-15"
    # }
    certification_info = models.JSONField(
        _("Certification & Permits"),
        default=dict,
        help_text=_("Stores Halal status, health permits, and inspection records."),
    )
    is_active = models.BooleanField(_("Is Active"), default=True)

    class Meta:
        db_table = "processing_plant"
        verbose_name = _("Processing Plant")
        indexes = [
            GinIndex(fields=["plant_config"], name="plant_config_gin_idx"),
            GinIndex(fields=["certification_info"], name="plant_cert_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Processing Plant '{self.name}' "
                f"from: {old_data} to: "
                f"{{'location': '{self.location}', 'manager': '{self.plant_manager}', 'config': {self.plant_config}}}"
            )
        return (
            f"Registered Processing Plant '{self.name}' "
            f"at location '{self.location}' managed by {self.plant_manager}"
        )

    def get_plant_details(self):
        return (
            f"{self.name.title()} ({self.location})"
            if self.name and self.location
            else f"{self.name}"
        )

    def __str__(self):
        return self.name


class ProcessingSession(BaseEnterpriseAuditModelMixin):
    """
    Tracks a specific slaughter/packaging run.
    Acts as the 'Converter' from Live Birds to Meat Inventory.
    """

    plant = models.ForeignKey(
        ProcessingPlant, on_delete=models.PROTECT, related_name="sessions"
    )

    source_batch = models.ForeignKey(
        "sfap.Batch",
        on_delete=models.PROTECT,
        related_name="processing_runs",
        verbose_name=_("Source Batch"),
    )
    assigned_workers = models.ManyToManyField(
        "hrms.Employee",
        related_name="session_workers",
        blank=True,
        verbose_name=_("Assigned Staff"),
    )

    birds_processed = models.PositiveIntegerField(_("Birds Processed"))
    live_birds_count = models.PositiveIntegerField(_("Live Birds Input"))
    total_live_weight = models.DecimalField(
        _("Live Weight (KG)"), max_digits=12, decimal_places=2
    )
    total_dressed_weight = models.DecimalField(
        _("Dressed Weight (KG)"), max_digits=12, decimal_places=2
    )

    # Blueprint for slaughter_data:
    # {
    #   "grade_a": 400, "grade_b": 50, "rejects": 5,
    #   "water_usage_liters": 1200,
    #   "cost_per_bird_slaughter": 200.00
    # }
    slaughter_data = models.JSONField(_("Slaughter Metrics"), default=dict)

    # Blueprint for environmental_logs:
    # {
    #   "scald_water_temp": 60.5,
    #   "stun_voltage": 110,
    #   "scald_time_sec": 120,
    #   "chiller_temp": 4.0,
    #   "defects_count": 5
    # }
    environmental_logs = models.JSONField(
        _("Processing Parameters"),
        default=dict,
        blank=True,
        help_text=_("Audit trail for water temperature, voltage, and safety metrics."),
    )

    start_time = models.DateTimeField(_("Session Start"))
    end_time = models.DateTimeField(_("Session End"))

    yield_percentage = models.DecimalField(
        _("Yield Percentage (%)"), max_digits=5, decimal_places=2, editable=False
    )
    temperature_recorder = models.CharField(_("Temperature Recorded"), max_length=100)
    rejected_birds = models.PositiveIntegerField(
        _("Rejects/Condemned"),
        default=0,
        help_text=_("Birds rejected during inspection for health/quality reasons."),
    )

    class Meta:
        db_table = "processing_session"
        verbose_name = _("Processing Session")
        ordering = ["-start_time"]
        indexes = [
            GinIndex(fields=["environmental_logs"], name="environmental_logs_gin_idx"),
        ]

    def clean(self):
        """Cross-checks bird counts and worker safety."""
        total_accounted = self.birds_processed + self.rejected_birds
        if total_accounted > self.live_birds_count:
            raise ValidationError(
                _(
                    f"Count Mismatch: You accounted for {total_accounted} birds, "
                    f"but only {self.live_birds_count} were received from the farm."
                )
            )

        if self.total_dressed_weight >= self.total_live_weight:
            raise ValidationError(
                _("Dressed weight cannot be greater than or equal to Live weight.")
            )

    def add_worker_to_session(self, worker):
        """Checks health clearance before adding worker to the M2M field."""
        if (
            not hasattr(worker, "employee_profile")
            or not worker.employee_profile.is_health_compliant
        ):
            raise ValidationError(_("Worker health clearance expired or missing."))
        self.assigned_workers.add(worker)

    def save(self, *args, **kwargs):
        # Calculate Yield (Dressed vs Live Weight)
        if self.total_live_weight and self.total_live_weight > 0:
            self.yield_percentage = (
                self.total_dressed_weight / self.total_live_weight
            ) * 100
        else:
            self.yield_percentage = 0

        # Ensure clean() is called even if not using a ModelForm
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def bird_loss_count(self) -> int:
        """Difference between birds received and birds successfully dressed."""
        return self.live_birds_count - self.birds_processed

    @property
    def slaughter_shrinkage_kg(self) -> float:
        """Calculates physical weight lost during processing (blood, feathers, etc)."""
        return self.total_live_weight - self.total_dressed_weight

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Processing Session at Plant '{self.plant.name}' "
                f"for Batch '{self.source_batch.batch_id}' "
                f"from: {old_data} to: birds processed {self.birds_processed}, "
                f"yield {self.yield_percentage:.2f}%"
            )
        return (
            f"Processing Session started at Plant '{self.plant.name}' "
            f"for Batch '{self.source_batch.batch_id}' — "
            f"{self.birds_processed} birds processed, dressed weight {self.total_dressed_weight}kg, "
            f"yield {self.yield_percentage:.2f}%"
        )
