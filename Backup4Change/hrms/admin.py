from django.contrib import admin
from .models import (
    Department, Employee, NextOfKin, UserIdentity
)
from guardian.admin import GuardedModelAdmin

# Register your models here.
# admin.site.register(Department)
admin.site.register(Employee)
admin.site.register(NextOfKin)
admin.site.register(UserIdentity)


@admin.register(Department)
class DepartmentAdmin(GuardedModelAdmin):
    list_display = ('name', 'created_by', 'is_active')
