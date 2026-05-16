from common.permissions.base import EnterpriseObjectLevelPermissionMixin
from common.mixins import BaseEnterpriseViewSet
from hrms.models import Department
from hrms.serializers import DepartmentSerializer


class DepartmentViewSet(EnterpriseObjectLevelPermissionMixin, BaseEnterpriseViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
