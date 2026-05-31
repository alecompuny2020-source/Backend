from django.db import models
from django.utils.translation import gettext_lazy as _

from common.mixins import BaseEnterpriseAuditModelMixin

# Create your models here.


class Department(BaseEnterpriseAuditModelMixin):
    """Core Employee Department model"""

    name = models.CharField(
        max_length=200, verbose_name=_("Department name"), unique=True
    )
    description = models.TextField(verbose_name=_("Department Description"))
    sub_department = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subordinates",
        verbose_name=_("Minor department"),
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        verbose_name=_("Department Code"),
        help_text=_("Unique short code for ID generation (e.g., HR, MFG, SLS, MKT)"),
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "department"
        verbose_name = _("Department")
        verbose_name_plural = _("Departments")
        ordering = ["-id"]

    def clean(self):
        """Force consistency at the model validation layer"""
        super().clean()
        if self.code:
            # Strip spaces and make uppercase (e.g., "  hr " -> "HR")
            self.code = self.code.strip().upper()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})"


class EmployeeIDSequence(models.Model):
    """Tracks the auto-incrementing sequence counter for each distinct prefix code."""

    prefix = models.CharField(
        max_length=10, unique=True, db_index=True, help_text="e.g., HR, MFG, SLS"
    )
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
