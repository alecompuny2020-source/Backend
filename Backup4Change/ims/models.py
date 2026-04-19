from django.db import models
from django.contrib.postgres.indexes import GinIndex
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from ..helpers import ASSET_TYPE_CHOICES, PRIORITY_CHOICES, STATUS_CHOICES
from ..utils import FarmAuditBaseModel

# Create your models here.

class MaintenanceRequest(FarmAuditBaseModel):
    """
    REACTIVE MAINTENANCE:
    Tracks the full lifecycle: Request -> Assignment -> Inspection -> Repair.
    """

    unit_id = models.PositiveIntegerField(_("Unit ID Ref"), db_index=True)
    zone_id = models.PositiveIntegerField(_("Zone ID Ref"), db_index=True)
    reported_by_id = models.PositiveIntegerField(
        _("Tenant/Staff ID Ref"), db_index=True
    )

    issue_description = models.TextField(_("Initial Issue Description"))
    priority = models.CharField(
        _("Priority"), max_length=20, choices=PRIORITY_CHOICES, default="NORMAL"
    )
    status = models.CharField(
        _("Repair Status"), max_length=20, choices=STATUS_CHOICES, default="OPEN"
    )

    # 1. TRACKING ASSIGNMENT & INSPECTION
    # Blueprint for inspection_data:
    # {
    #    "assigned_to_staff_id": 102,
    #    "assigned_at": "2026-03-05T10:00:00Z",
    #    "inspection_date": "2026-03-06",
    #    "inspection_findings": "Leaking valve in the primary cooling line. Corrosion detected.",
    #    "urgency_score": 9,
    #    "requires_external_contractor": false
    # }
    inspection_data = models.JSONField(
        _("Inspection & Assignment"),
        default=dict,
        blank=True,
        help_text=_(
            "Tracks who is assigned and what they found during the initial survey."
        ),
    )

    # 2. TRACKING MAINTENANCE METADATA (AFTER WORK)
    # Blueprint for maintenance_metadata:
    # {
    #    "completion_date": "2026-03-07",
    #    "work_performed": "Replaced valve and cleaned surrounding pipework.",
    #    "parts_replaced": [{"name": "Valve A1", "cost": 4500}, {"name": "Sealant", "cost": 500}],
    #    "total_labor_hours": 3.5,
    #    "contractor_invoice_ref": "INV-9901",
    #    "final_safety_check_passed": true,
    #   "before_photos": ["cdn.url/img1.jpg"],
    #    "after_photos": ["cdn.url/img2.jpg"],
    #    "signature_url": "cdn.url/staff_sig.png"
    # }
    maintenance_metadata = models.JSONField(
        _("Post-Maintenance Data"),
        default=dict,
        blank=True,
        help_text=_("Detailed breakdown of parts, labor, and final resolution."),
    )

    class Meta:
        db_table = "maintenance_request"
        verbose_name = _("Maintenance Request")
        # GIN Indexes for high-speed search across findings and parts
        indexes = [
            GinIndex(fields=["inspection_data"], name="maint_inspect_gin_idx"),
            GinIndex(fields=["maintenance_metadata"], name="maint_work_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Maintenance Request REQ-{self.id} "
                f"from: {old_data} to: status {self.status}, priority {self.priority}, "
                f"issue '{self.issue_description}'"
            )
        if self.status == "COMPLETED":
            return (
                f"Maintenance Request REQ-{self.id} completed — "
                f"work performed: {self.maintenance_metadata.get('work_performed')}, "
                f"completion date: {self.maintenance_metadata.get('completion_date')}"
            )
        return (
            f"Created Maintenance Request REQ-{self.id} "
            f"for Unit {self.unit_id}, Zone {self.zone_id}, "
            f"issue: '{self.issue_description}', priority {self.priority}, status {self.status}"
        )

    def __str__(self):
        return f"REQ-{self.id}: {self.priority} - {self.status}"


class MaintenanceLog(FarmAuditBaseModel):
    """
    PROACTIVE MAINTENANCE & AUDIT:
    Universal log for Farms, Buildings, Zones, and Units.
    Lives in: amenities_db (serving as the central Facility Management vault).
    """

    # 1. UNIVERSAL ASSET LINK (Soft References for Multi-DB)
    asset_type = models.CharField(
        _("Asset Type"), max_length=20, choices=ASSET_TYPE_CHOICES, db_index=True
    )
    asset_id = models.PositiveIntegerField(
        _("Asset ID Reference"),
        db_index=True,
        help_text=_("The ID of the Farm, Building, Zone, or Unit being inspected."),
    )

    # 2. INSPECTION LOGISTICS
    inspection_date = models.DateField(_("Inspection Date"))
    inspector_id = models.PositiveIntegerField(_("Staff ID Ref"), db_index=True)

    # 3. THE DYNAMIC REPORT (Point #8: JSONB + GIN)
    # The blueprint changes based on asset_type:
    # FARM: {"biosecurity_check": "PASS", "fence_intact": true}
    # ZONE: {"swings_status": "Safe", "pool_ph": 7.2}
    # UNIT: {"smoke_detector_battery": "OK", "leaks_found": false}
    report = models.JSONField(
        _("Inspection Report"),
        default=dict,
        help_text=_("Asset-specific safety findings and health scores."),
    )

    # 4. MAINTENANCE METADATA (The "After" / Post-Survey)
    # Tracks what was actually fixed following the inspection.

    maintenance_metadata = models.JSONField(
        _("Maintenance Metadata"),
        default=dict,
        blank=True,
        help_text=_("Records of parts replaced, labor, and costs incurred."),
    )
    total_cost = MoneyField(
        _("Total Maintenance Cost"),
        max_digits=14,
        decimal_places=2,
        default_currency="TZS",
        default=0.00,
    )

    class Meta:
        db_table = "maintenance_log"
        verbose_name = _("Maintenance Log")
        ordering = ["-created_on"]
        indexes = [
            # GIN Indexes allow fast searching of specific issues across all asset types
            GinIndex(fields=["report"], name="maint_log_report_gin_idx"),
            GinIndex(fields=["maintenance_metadata"], name="maint_log_meta_gin_idx"),
        ]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Maintenance Log for Asset {self.asset_type} (ID {self.asset_id}) "
                f"from: {old_data} to: inspection {self.inspection_date}, "
                f"report {self.report}, total cost {self.total_cost}"
            )
        return (
            f"Recorded Maintenance Log for Asset {self.asset_type} (ID {self.asset_id}) "
            f"on {self.inspection_date} by Staff {self.inspector_id}, "
            f"report {self.report}, total cost {self.total_cost}"
        )

    def save(self, *args, **kwargs):
        """
        Summarizes the financial impact of the maintenance.
        Expected JSON: {"parts": [{"cost": 1000}], "labor_cost": 5000}
        """
        # 1. Sum up parts costs
        parts = self.maintenance_metadata.get("parts", [])
        parts_total = sum(Decimal(str(p.get("cost", 0))) for p in parts)

        # 2. Add labor cost
        labor_cost = Decimal(str(self.maintenance_metadata.get("labor_cost", 0)))

        # 3. Finalize total cost for the Accountant
        self.total_cost = parts_total + labor_cost

        super().save(*args, **kwargs)
