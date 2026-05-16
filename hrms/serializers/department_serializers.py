from common.mixins import BaseEnterpriseAuditSerializer
from hrms.models import Department


class DepartmentSerializer(BaseEnterpriseAuditSerializer):
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'description', 'sub_department', 'is_active',
            'created_by', 'updated_by', 'created_on', 'updated_on'
        ]
