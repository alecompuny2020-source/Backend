from datetime import timedelta

from django.contrib.postgres.indexes import GinIndex
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from common.constants import now
from common.mixins import BaseEnterpriseAuditModelMixin


class HealthProtocol(BaseEnterpriseAuditModelMixin):
    """
    Standardized health procedures (e.g., Gumboro Vaccination Protocol).
    Acts as a template for automated reminders.
    """

    name = models.CharField(_("Protocol Name"), max_length=255)
    target_bird_type = models.ForeignKey("config.BirdType", on_delete=models.RESTRICT)

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


class MedicalRecord(BaseEnterpriseAuditModelMixin):
    """
    Tracks specific health events. Links directly to Accounting for 'Cost per Bird' analysis.
    """

    batch = models.ForeignKey(
        "sfap.Batch",
        on_delete=models.CASCADE,
        related_name="health_records",
        verbose_name=_("Flock Batch"),
    )
    date_of_administration = models.DateField(
        _("Date of Administration"), db_index=True, default=now
    )
    status = models.ForeignKey("config.HealthRecordType", on_delete=models.RESTRICT)

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
        verbose_name_plural = _("Medical Records")
        indexes = [
            GinIndex(fields=["event_details"], name="medical_event_gin_idx"),
        ]

    @property
    def is_in_withdrawal(self) -> bool:
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


class DiseaseOutbreak(BaseEnterpriseAuditModelMixin):
    """
    Quarantine and Emergency Alerts.
    Triggers notifications to the Farm Manager and Vet.
    """

    batch = models.ForeignKey(
        "sfap.Batch",
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
    status = models.ForeignKey(
        "config.DiseaseOutbreakStatus", on_delete=models.RESTRICT
    )

    class Meta:
        db_table = "disease_outbreak"
        verbose_name = _("Disease Outbreak")
        verbose_name_plural = _("Disease Outbreaks")
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
