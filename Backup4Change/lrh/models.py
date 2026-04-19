from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from helpers.choices import REGISTRATION_STATUS
from helpers.validators import (upload_employee_contract_document, contact_validator, validate_contract_mime)
from utils.mixins import ActionTrackingBaseModelMixin
from hrms.models import Employee

# Create your models here.

class EmployeeRegistrationHistory(ActionTrackingBaseModelMixin):
    """
    Tracks the formal registration, verification, and onboarding
    lifecycle of a farm employee.
    """

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="registration_logs"
    )
    status = models.CharField(
        max_length=20, choices=REGISTRATION_STATUS, default="PENDING"
    )
    remarks = models.TextField(
        _("Registration Remarks"),
        blank=True,
        help_text=_("Notes regarding background checks or verification details."),
    )
    contract_document = models.FileField(
        upload_to=upload_employee_contract_document,
        validators=[contact_validator, validate_contract_mime],
        null=True,
        blank=True,
        help_text=_("Upload the signed employment contract (PDF/JPG)."),
    )

    class Meta:
        db_table = "audit_employee_registration"
        verbose_name = _("Employee Registration History")
        ordering = ["-initiated_at"]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Employee Registration for {self.employee} "
                f"from status: {old_data.get('status')} to: {self.status}"
            )
        if self.registered_at and self.registered_by:
            return f"Employee {self.employee} formally registered with contract {self.contract_document or 'N/A'}"
        if self.verified_at and self.verified_by:
            return f"Employee {self.employee} registration verified"
        return f"Initiated Employee Registration for {self.employee} (status: {self.status})"


# class TenantRegistrationHistory(FarmAuditBaseModelMixin):
#     """
#     Tracks when a tenant (e.g., someone renting farm space or stalls)
#     is initiated, verified, and officially registered in the system.
#     """
#
#     tenant = models.ForeignKey(
#         settings.TENANT_REFERENCE,
#         on_delete=models.CASCADE,
#         related_name="registration_logs",
#     )
#     contract_reference = models.CharField(_("Contract Ref"), max_length=100, blank=True)
#
#     class Meta:
#         db_table = "audit_tenant_registration"
#         verbose_name = _("Tenant Registration History")
#         ordering = ["-initiated_at"]
#
#     def clean(self):
#         """Ensure a contract reference exists before marking as Verified."""
#         if self.status == "VERIFIED" and not self.contract_reference:
#             raise ValidationError(
#                 _("Cannot verify tenant without a Contract Reference number.")
#             )
#
#     def get_log_message(self, old_data=None):
#         if old_data:
#             return (
#                 f"Updated Tenant Registration for {self.tenant} "
#                 f"from status: {old_data.get('status')} to: {self.status}"
#             )
#         if self.registered_at and self.registered_by:
#             return f"Tenant {self.tenant} formally registered with contract reference {self.contract_reference or 'N/A'}"
#         if self.verified_at and self.verified_by:
#             return f"Tenant {self.tenant} registration verified"
#         return (
#             f"Initiated Tenant Registration for {self.tenant} (status: {self.status})"
#         )
#
#     def save(self, *args, **kwargs):
#         self.full_clean()
#         super().save(*args, **kwargs)
