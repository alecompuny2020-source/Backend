from django.db import models
from django.utils.translation import gettext_lazy as _
from common.mixins import BaseEnterpriseAuditModelMixin

# Create your models here.

class Department(BaseEnterpriseAuditModelMixin):
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


class EmployeeIDSequence(models.Model):
    """Tracks the auto-incrementing sequence counter for each distinct prefix code."""
    prefix = models.CharField(max_length=10, unique=True, db_index = True, help_text="e.g., HR, MFG, SLS")
    last_sequence = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "employee_id_sequence"
        verbose_name = _("Employee ID Sequence")
        verbose_name_plural = _("Employee ID Sequences")

    def clean(self):
        # Force uniform consistency in the database layer
        if self.prefix:
            self.prefix = self.prefix.strip().upper()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.prefix} - Last: {self.last_sequence}"
