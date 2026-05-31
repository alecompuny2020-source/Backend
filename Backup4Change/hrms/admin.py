from django.contrib import admin
from guardian.admin import GuardedModelAdmin

from .models import Department, Employee, NextOfKin, UserIdentity

# Register your models here.
# admin.site.register(Department)
admin.site.register(Employee)
admin.site.register(NextOfKin)
admin.site.register(UserIdentity)


@admin.register(Department)
class DepartmentAdmin(GuardedModelAdmin):
    list_display = ("name", "created_by", "is_active")
