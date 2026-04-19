from django.db import models
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from phonenumber_field.modelfields import PhoneNumberField
from helpers.validators import (upload_personal_id, IDs_scan_validator, validate_scan_mime)
from helpers.choices import (
    CURRENCY_CHOICES, EMPLOYMENT_TYPES, TITLE_CHOICES, MARITAL_STATUSES,
    GENDER_CHOICES, ID_TYPES
    )
from ppms.models import ProcessingPlant
from sfap.models import FarmShed
from utils.mixins import FarmAuditBaseModelMixin


# Create your models here.

class Department(FarmAuditBaseModelMixin):
    """ Core Employee Department model """
    name = models.CharField(max_length = 200, verbose_name=_("Department name"), unique = True)
    description = models.TextField(verbose_name=_("Department Description"))
    sub_department = models.ForeignKey('self', on_delete = models.SET_NULL, null = True, blank = True, related_name="subordinates",
    verbose_name=_("Minor department"))
    is_active = models.BooleanField(default = True)

    def __str__(self):
        return f"{self.name} by {self.created_by}"

    class Meta:
        db_table = "department"
        verbose_name = _("Department")
        verbose_name_plural = _("Departments")
        ordering = ["created_by"]



class Employee(models.Model):
    """Core HR profile"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employee_profile",
        verbose_name=_("User"),
    )

    manager = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subordinates",
        verbose_name=_("Reports To"),
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        default = '1',
        related_name="departments",
        verbose_name=_("Employee Department"),
    )

    employee_number = models.CharField(
        _("Employee Number"), max_length=20, unique=True, db_index=True
    )

    marital_status = models.CharField(
        _("Marital Status"), max_length=20, choices = MARITAL_STATUSES, db_index=True,
        default = 'single'
    )
    employment_type = models.CharField(
        _("Employment Type"),
        max_length=20,
        choices=EMPLOYMENT_TYPES,
        default="FULL_TIME",
        help_text=_(
            "Determines benefits eligibility; e.g., Casuals usually don't get housing."
        ),
    )

    assigned_shed = models.ForeignKey(
        FarmShed,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_workers",
        verbose_name=_("Assigned Shed"),
    )

    assigned_plant = models.ForeignKey(
        ProcessingPlant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_workers",
        verbose_name=_("Assigned Processing Plant"),
    )
    health_clearance_expiry = models.DateField(
        _("Health Clearance Expiry"),
        null=True,
        blank=True,
        help_text=_("Required for Processing Plant staff. Must be renewed annually."),
    )
    employee_title = models.CharField(
        _("Employee Title"), max_length=20, choices = TITLE_CHOICES, db_index=True, null = True
    )
    gender = models.CharField(
        _("Employee Gender"), max_length=20, choices = GENDER_CHOICES, null = True
    )

    hire_date = models.DateField(_("Hire Date"))
    base_salary = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="TZS",
        verbose_name=_("Base Salary"),
    )
    is_active = models.BooleanField(
        _("Employment Status"),
        default=True,
        help_text=_("Uncheck this instead of deleting the employee for audit history."),
    )

    # --- Flexible HR Data (The 'Sweet' Logic) ---
    # Blueprint for hr_metadata:
    # {
    #   "emergency_contact": {"name": "...", "phone": "..."},
    #   "id_details": {"type": "NIDA", "number": "12345"},
    #   "skills": ["Slaughter", "Vaccination", "Data Entry"],
    #   "bank_name": "Christian",
    #   "payroll_config": {
    #       "bank_name": "NMB",
    #       "account_currency": "TZS",
    #       "salary_basis": "monthly"
    #   }
    # }
    hr_metadata = models.JSONField(
        _("HR Metadata"),
        default=dict,
        blank=True,
        help_text=_(
            "Stores emergency contacts, ID numbers, skills, and payroll configurations."
        ),
    )

    class Meta:
        db_table = "employee"
        verbose_name = _("Employee")
        verbose_name_plural = _("Employees")
        ordering = ["employee_number"]
        indexes = [
            GinIndex(fields=["hr_metadata"], name="emp_hr_meta_gin_idx"),
        ]
        permissions = [
            ("can_deactivate_employee", "Can deactivate employee"),
            ("can_change_employee_department", "Can change employee department"),
            ("can_change_employee_type", "Can change employee type"),
            ("can_assign_shed", "Can assign shed"),
            ("can_change_shed", "Can change shed"),
            ("can_assign_plant", "Can assign plant"),
            ("can_change_plant", "Can change plant"),
            ("can_add_health_clearance", "Can add health clearance"),
            ("can_add_salary", "Can add salary"),
            ("can_change_salary", "Can change salary"),
        ]

    @property
    def current_bird_load(self):
        """Returns total number of live birds in the employee's assigned shed."""
        if self.assigned_shed:
            # Sum current_count of all active batches in that shed
            return (
                self.assigned_shed.batches.filter(status="ACTIVE").aggregate(
                    total=models.Sum("current_count")
                )["total"]
                or 0
            )
        return 0

    @property
    def is_health_compliant(self):
        """Checks if the employee's health certificate is still valid."""
        if not self.health_clearance_expiry:
            return False
        return self.health_clearance_expiry >= timezone.now().date()

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Employee '{self.user.get_full_name()}' "
                f"from: {old_data} to: "
                f"{{'employee_number': '{self.employee_number}', 'employment_type': '{self.employment_type}', 'salary': '{self.base_salary}'}}"
            )
        return (
            f"Registered Employee '{self.user.get_full_name()}' "
            f"with number {self.employee_number}, type {self.employment_type}, "
            f"salary {self.base_salary}"
        )

    def get_employee_display(self):
        """Returns a formatted string with the employee's title and full name."""

        employee_name = self.user.get_full_name()
        employee_title = self.employee_title.title() if self.employee_title else ""
        return f"{employee_title} {employee_name}".strip()

    def __str__(self):
        return self.get_employee_display()


class NextOfKin(models.Model):
    """
    Stores contact information for a user's next of kin.
    Linked to the custom user model defined in settings.
    """

    owner = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="next_of_kin_contacts",
        verbose_name=_("user"),
        help_text=_("The user this next of kin belongs to"),
    )
    first_name = models.CharField(max_length=100, verbose_name=_("first name"))
    middle_name = models.CharField(max_length=100, verbose_name=_("middle name"))
    last_name = models.CharField(max_length=100, verbose_name=_("last name"))
    phone_number = PhoneNumberField(
        verbose_name=_("phone number"),
        help_text=_("Enter phone number in international format (e.g. +255...)"),
    )
    email = models.EmailField(null=True, blank=True, verbose_name=_("email address"))
    physical_address = models.CharField(
        max_length=200, verbose_name=_("physical address")
    )

    class Meta:
        db_table = "next_of_kin"
        verbose_name = _("Next of Kin")
        verbose_name_plural = _("Next of Kin")
        ordering = ["first_name", "middle_name", "last_name"]

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Next of Kin for {self.user.get_full_name()} "
                f"from: {old_data} to: {self.first_name} {self.last_name}, {self.phone_number}"
            )
        return (
            f"Added Next of Kin '{self.first_name} {self.last_name}' "
            f"for {self.user.get_full_name()} (Phone: {self.phone_number})"
        )

    def __str__(self):
        return _("%(first)s %(last)s - Kin of %(user)s") % {
            "first": self.first_name,
            "last": self.last_name,
            "user": self.owner.user.get_full_name(),
        }


class UserIdentity(models.Model):
    """ Allows user to have multiple forms of ID (NIDA, Passport, MPIGA KURA etc.) """

    owner = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="identities",
        verbose_name=_("User"),
    )
    identity_type = models.CharField(
        _("Identity Type"), max_length=20, choices=ID_TYPES
    )
    identity_number = models.CharField(
        _("Identity Number"), max_length=50, db_index=True
    )
    expiry_date = models.DateField(_("Expiry Date"), null=True, blank=True)
    # Optional: If the scan of the ID is required
    id_image = models.ImageField(
        _("ID Scan/Photo"),
        upload_to = upload_personal_id,
        validators = [IDs_scan_validator, validate_scan_mime],
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "employee_identity"
        verbose_name = _("Employee Identity")
        verbose_name_plural = _("Employee Identities")
        unique_together = ("owner", "identity_type")

    def clean(self):
        """Validate ID expiry."""
        if self.expiry_date and self.expiry_date < timezone.now().date():
            raise ValidationError(_("This identity document has already expired."))

    def get_log_message(self, old_data=None):
        if old_data:
            return f"Updated Identity {self.identity_type} from: {old_data} to: {self.identity_number}"
        return f"Added Identity {self.identity_type} : {self.identity_number}"

    @property
    def is_valid(self):
        if not self.expiry_date:
            return True
        return self.expiry_date >= timezone.now().date()

    def __str__(self):
        return f"{self.identity_type}: {self.identity_number}"


# class WorkShift(models.Model):
#     """
#     Tracks attendance and labor hours.
#     Crucial for cost-allocation in the Accounting Module.
#     Attendance ledger. Links hours worked to specific tasks/costs.
#     """
#
#     employee = models.ForeignKey(
#         settings.FARM_WORKER,
#         on_delete=models.CASCADE,
#         related_name="shifts",
#         verbose_name=_("Employee"),
#     )
#
#     clock_in = models.DateTimeField(_("Clock In"), default=timezone.now)
#     clock_out = models.DateTimeField(_("Clock Out"), null=True, blank=True)
#
#     # --- Task & Cost Logic (The 'Sweet' Details) ---
#     # Blueprint for task_log:
#     # [
#     #   {
#     #     "task_id": "FEEDING_01",
#     #     "task_name": "Feeding Layers",
#     #     "duration_minutes": 120,
#     #     "location_id": "SHED_A",
#     #     "allocated_cost": 5000.00,
#     #     "currency": "TZS"
#     #   }
#     # ]
#     task_log = models.JSONField(
#         _("Task Log"),
#         default=list,
#         help_text=_(
#             "List of completed tasks with duration and location for cost accounting."
#         ),
#     )
#
#     # Blueprint for performance_metrics:
#     # {
#     #   "incident_reports": 0,
#     #   "supervisor_rating": 5,
#     #   "late_minutes": 15,
#     #   "overtime_eligible": true,
#     #   "verified_by_kiosk_id": "KIOSK_DODOMA_01"
#     # }
#     performance_metrics = models.JSONField(
#         _("Performance Metrics"),
#         default=dict,
#         blank=True,
#         help_text=_("Stores incident reports, ratings, and kiosk verification data."),
#     )
#
#     class Meta:
#         db_table = "work_shift"
#         verbose_name = _("Work Shift")
#         verbose_name_plural = _("Work Shifts")
#         ordering = ["-clock_in"]
#         indexes = [
#             GinIndex(fields=["task_log"], name="shift_task_log_gin_idx"),
#             GinIndex(fields=["performance_metrics"], name="shift_perf_gin_idx"),
#         ]
#
#     @property
#     def total_duration(self):
#         """Calculates total shift time for payroll processing."""
#         if self.clock_in and self.clock_out:
#             return self.clock_out - self.clock_in
#         return None
#
#     def get_log_message(self, old_data=None):
#         if old_data:
#             return (
#                 f"Updated Work Shift for {self.employee.get_full_name()} "
#                 f"from: {old_data} to: clock-in {self.clock_in}, clock-out {self.clock_out}"
#             )
#         if self.clock_out:
#             return (
#                 f"Work Shift completed for {self.employee.get_full_name()} "
#                 f"from {self.clock_in} to {self.clock_out}, tasks: {self.task_log}"
#             )
#         return (
#             f"Work Shift started for {self.employee.get_full_name()} "
#             f"at {self.clock_in}, tasks logged: {self.task_log}"
#         )
#
#     def __str__(self):
#         return f"{self.employee.user.get_full_name()} - {self.clock_in.strftime('%Y-%m-%d')}"
#
#
# class PayrollRecord(models.Model):
#     """
#     Links labor to the Accounting System.
#     """
#
#     employee = models.ForeignKey(
#         settings.FARM_WORKER,
#         on_delete=models.PROTECT,
#         related_name="payroll_records",
#         verbose_name=_("Employee"),
#     )
#
#     pay_period_start = models.DateField(_("Pay Period Start"))
#     pay_period_end = models.DateField(_("Pay Period End"))
#     pay_period_days = models.PositiveIntegerField(
#         _("Days in Period"),
#         default=30,
#         help_text=_(
#             "Number of days worked in this cycle. Used for pro-rating salaries."
#         ),
#     )
#
#     base_salary = MoneyField(
#         verbose_name=_("Base Salary"),
#         max_digits=12,
#         decimal_places=2,
#         default_currency="TZS",
#     )
#     bonuses = MoneyField(
#         verbose_name=_("Bonuses"),
#         max_digits=12,
#         decimal_places=2,
#         default=0,
#         default_currency="TZS",
#     )
#     deductions = MoneyField(
#         verbose_name=_("Deductions"),
#         max_digits=12,
#         decimal_places=2,
#         default=0,
#         default_currency="TZS",
#     )
#     housing_deduction = MoneyField(
#         _("Housing Deduction"),
#         max_digits=14,
#         decimal_places=2,
#         default=0,
#         default_currency="TZS",
#         help_text=_("Amount deducted for staff quarters, linked to Housing Module."),
#     )
#
#     # --- Benefits & Deductions (The 'Sweet' Details) ---
#     # Blueprint for benefits_breakdown:
#     # {
#     #   "allowances": {"housing": 50000, "transport": 20000},
#     #   "statutory": {"nssf": 10000, "paye": 5000},
#     #   "insurance": {"nhif": 3000},
#     #   "exchange_rate_at_runtime": 1.0,
#     #   "conversion_notes": "Paid in TZS, reported in GBP"
#     # }
#     benefits_breakdown = models.JSONField(
#         _("Benefits & Deductions Breakdown"),
#         default=dict,
#         help_text=_(
#             "Detailed JSON map of allowances, taxes (NSSF/PAYE), and insurance."
#         ),
#     )
#
#     # --- Status ---
#     is_paid = models.BooleanField(_("Payment Status"), default=False)
#     payment_date = models.DateTimeField(_("Payment Date"), null=True, blank=True)
#
#     # Blueprint for payment_metadata:
#     # {
#     #   "bank_reference": "TXN_992831",
#     #   "payment_method": "Mobile Money / Bank Transfer",
#     #   "authorized_by_id": "UUID_OF_ACCOUNTANT",
#     #   "attendance_percentage": 98,
#     #   "performance_bonus_trigger": true,
#     #   "manager_approval_signature": "SIG_UUID_99",
#     #   "overtime_hours": 12
#     # }
#     payment_metadata = models.JSONField(
#         _("Payment Metadata"),
#         default=dict,
#         blank=True,
#         help_text=_("Audit trail for bank references and authorization IDs."),
#     )
#
#     class Meta:
#         db_table = "payroll_record"
#         verbose_name = _("Payroll Record")
#         verbose_name_plural = _("Payroll Records")
#         ordering = ["-pay_period_end"]
#         indexes = [
#             GinIndex(fields=["benefits_breakdown"], name="payroll_benefits_gin_idx"),
#             GinIndex(fields=["payment_metadata"], name="payroll_pay_meta_gin_idx"),
#         ]
#
#     @property
#     def net_pay(self):
#         """Calculates the final amount to be disbursed.
#         Formula: (Base + Allowances) - (Taxes + Housing)
#         """
#         total_earnings = self.base_salary  # plus allowances from JSON
#         total_deductions = self.housing_deduction  # plus taxes from JSON
#         return total_earnings - total_deductions
#
#     def calculate_pro_rated_base(self):
#         """
#         Example logic: Calculates base pay adjusted for days worked.
#         Formula: (Monthly Base / 30) * pay_period_days
#         """
#         daily_rate = self.base_salary / 30
#         return daily_rate * self.pay_period_days
#
#     def get_log_message(self, old_data=None):
#         if old_data:
#             return (
#                 f"Updated Payroll Record for {self.employee.get_full_name()} "
#                 f"from: {old_data} to: base salary {self.base_salary}, bonuses {self.bonuses}, deductions {self.deductions}"
#             )
#         if self.is_paid and self.payment_date:
#             return (
#                 f"Payroll Record finalized for {self.employee.get_full_name()} "
#                 f"period {self.pay_period_start} to {self.pay_period_end}, "
#                 f"net pay {self.net_pay}, paid on {self.payment_date}"
#             )
#         return (
#             f"Created Payroll Record for {self.employee.get_full_name()} "
#             f"period {self.pay_period_start} to {self.pay_period_end}, "
#             f"base salary {self.base_salary}, bonuses {self.bonuses}, deductions {self.deductions}"
#         )
#
#     def __str__(self):
#         return f"{self.employee.user.get_full_name()} - {self.pay_period_end} ({self.currency})"
