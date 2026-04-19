from rest_framework import serializers
from .models import Department, NextOfKin, UserIdentity
from rest_framework_guardian.serializers import ObjectPermissionsAssignmentMixin
from guardian.shortcuts import assign_perm
from django.contrib.auth.models import Group


class DepartmentSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ['name', 'description', 'created_by', 'created_at', 'sub_department']

    def get_created_by(self, obj) -> str:
        return obj.created_by.get_full_name() if obj.created_by else None

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user
        department = Department.objects.create(**validated_data)

        return department


class NextOfKinSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()

    class Meta:
        model = NextOfKin
        fields = [
            'id', 'owner', 'first_name', 'middle_name', 'last_name',
            'phone_number', 'email', 'physical_address'
        ]
        extra_kwargs = {
            "read_only_fields" : {'id', 'owner'}
        }

        def get_owner(self, obj) -> str:
            return obj.owner.user.get_full_name() if obj.owner.user else 'Employee'

        def create(self, validated_data):
            request = self.context['request']
            user = request.user
            if hasattr(user, 'employee_profile'):
                emp = user.employee_profile
                validated_data['owner'] = emp
                kin = NextOfKin.objects.create(**validated_data)

            return kin


class UserIdentitySerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()

    class Meta:
        model = UserIdentity
        fields = ['id', 'owner', 'identity_type', 'identity_number', 'expiry_date', 'id_image']
        extra_kwargs = {
            "read_only_fields" : {'id', 'owner'}
        }

    def get_owner(self, obj) -> str:
        return obj.owner.user.get_full_name() if obj.owner.user else 'Employee'

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        if hasattr(user, 'employee_profile'):
            emp = user.employee_profile
            validated_data['owner'] = emp
            identity = UserIdentity.objects.create(**validated_data)

        return identity
