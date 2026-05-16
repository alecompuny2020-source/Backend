from common.mixins import BaseEnterpriseModelMixin
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


# class Employee(BaseEnterpriseModelMixin):
#     """Core HR profile"""
#
#     user = models.OneToOneField(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name="employee_profile",
#         verbose_name=_("User"),
#     )
#
#     manager = models.ForeignKey(
#         "self",
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="subordinates",
#         verbose_name=_("Reports To"),
#     )
#
#     department = models.ForeignKey(
#         'hrms.Department',
#         on_delete=models.PROTECT,
#         related_name="departments",
#         verbose_name=_("Employee Department"),
#     )
#
#     employee_number = models.CharField(
#         _("Employee Number"), max_length=20, unique=True, db_index=True
#     )
#
#     marital_status = models.CharField(
#         _("Marital Status"), max_length=20, choices = MARITAL_STATUSES, db_index=True,
#         default = 'single'
#     )
#     employment_type = models.CharField(
#         _("Employment Type"),
#         max_length=20,
#         choices=EMPLOYMENT_TYPES,
#         default="FULL_TIME",
#         help_text=_(
#             "Determines benefits eligibility; e.g., Casuals usually don't get housing."
#         ),
#     )
#
#     assigned_shed = models.ForeignKey(
#         FarmShed,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="assigned_workers",
#         verbose_name=_("Assigned Shed"),
#     )
#
#     assigned_plant = models.ForeignKey(
#         ProcessingPlant,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="assigned_workers",
#         verbose_name=_("Assigned Processing Plant"),
#     )
#     health_clearance_expiry = models.DateField(
#         _("Health Clearance Expiry"),
#         null=True,
#         blank=True,
#         help_text=_("Required for Processing Plant staff. Must be renewed annually."),
#     )
#     employee_title = models.CharField(
#         _("Employee Title"), max_length=20, choices = TITLE_CHOICES, db_index=True, null = True
#     )
#     gender = models.CharField(
#         _("Employee Gender"), max_length=20, choices = GENDER_CHOICES, null = True
#     )
#
#     hire_date = models.DateField(_("Hire Date"))
#     base_salary = MoneyField(
#         max_digits=14,
#         decimal_places=2,
#         default_currency="TZS",
#         verbose_name=_("Base Salary"),
#     )
#     is_active = models.BooleanField(
#         _("Employment Status"),
#         default=True,
#         help_text=_("Uncheck this instead of deleting the employee for audit history."),
#     )
#
#     # --- Flexible HR Data (The 'Sweet' Logic) ---
#     # Blueprint for hr_metadata:
#     # {
#     #   "emergency_contact": {"name": "...", "phone": "..."},
#     #   "id_details": {"type": "NIDA", "number": "12345"},
#     #   "skills": ["Slaughter", "Vaccination", "Data Entry"],
#     #   "bank_name": "Christian",
#     #   "payroll_config": {
#     #       "bank_name": "NMB",
#     #       "account_currency": "TZS",
#     #       "salary_basis": "monthly"
#     #   }
#     # }
#     hr_metadata = models.JSONField(
#         _("HR Metadata"),
#         default=dict,
#         blank=True,
#         help_text=_(
#             "Stores emergency contacts, ID numbers, skills, and payroll configurations."
#         ),
#     )
#
#     class Meta:
#         db_table = "employee"
#         verbose_name = _("Employee")
#         verbose_name_plural = _("Employees")
#         ordering = ["employee_number"]
#         indexes = [
#             GinIndex(fields=["hr_metadata"], name="emp_hr_meta_gin_idx"),
#         ]
#         permissions = [
#             ("can_deactivate_employee", "Can deactivate employee"),
#             ("can_change_employee_department", "Can change employee department"),
#             ("can_change_employee_type", "Can change employee type"),
#             ("can_assign_shed", "Can assign shed"),
#             ("can_change_shed", "Can change shed"),
#             ("can_assign_plant", "Can assign plant"),
#             ("can_change_plant", "Can change plant"),
#             ("can_add_health_clearance", "Can add health clearance"),
#             ("can_add_salary", "Can add salary"),
#             ("can_change_salary", "Can change salary"),
#         ]
#
#     @property
#     def current_bird_load(self):
#         """Returns total number of live birds in the employee's assigned shed."""
#         if self.assigned_shed:
#             # Sum current_count of all active batches in that shed
#             return (
#                 self.assigned_shed.batches.filter(status="ACTIVE").aggregate(
#                     total=models.Sum("current_count")
#                 )["total"]
#                 or 0
#             )
#         return 0
#
#     @property
#     def is_health_compliant(self):
#         """Checks if the employee's health certificate is still valid."""
#         if not self.health_clearance_expiry:
#             return False
#         return self.health_clearance_expiry >= timezone.now().date()
#
#     def get_log_message(self, old_data=None):
#         if old_data:
#             return (
#                 f"Updated Employee '{self.user.get_full_name()}' "
#                 f"from: {old_data} to: "
#                 f"{{'employee_number': '{self.employee_number}', 'employment_type': '{self.employment_type}', 'salary': '{self.base_salary}'}}"
#             )
#         return (
#             f"Registered Employee '{self.user.get_full_name()}' "
#             f"with number {self.employee_number}, type {self.employment_type}, "
#             f"salary {self.base_salary}"
#         )
#
#     def get_employee_display(self):
#         """Returns a formatted string with the employee's title and full name."""
#
#         employee_name = self.user.get_full_name()
#         employee_title = self.employee_title.title() if self.employee_title else ""
#         return f"{employee_title} {employee_name}".strip()
#
#     def __str__(self):
#         return self.get_employee_display()
