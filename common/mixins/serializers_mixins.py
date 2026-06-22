from rest_framework import serializers

from common.utils import enforce_password


class BaseRegistrationSerializer(serializers.ModelSerializer):
    """Performs self-user registration (for customers and non-staff users) and generates the initial OTP."""

    first_name = serializers.CharField()
    last_name = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        """Enforces password Policy"""
        return enforce_password(value)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        model = self.Meta.model
        user_fields = ["first_name", "last_name", "password"]

        for field_name in user_fields:
            if not hasattr(model, field_name):
                self.fields.pop(field_name, None)

    def validate(self, attrs):
        first_name = attrs.get("first_name", "").strip()
        last_name = attrs.get("last_name", "").strip()

        if not first_name or not last_name:
            raise serializers.ValidationError(
                {"names": _("Both first name and last name are required.")}
            )

        if not first_name.isalpha() or not last_name.isalpha():
            raise serializers.ValidationError(
                {"names": _("Names must contain only letters.")}
            )

        return attrs

    def create(self, validated_data):
        """Perform creation of user instance"""
        return self.Meta.model.objects.create_user(**validated_data)


class BaseEnterpriseAuditSerializer(serializers.ModelSerializer):
    """
    A dynamic base serializer that automatically exposes audit fields if they
    exist on the model, using 'created_by' and 'updated_by' for user full names.
    """

    created_by = serializers.CharField(
        source="created_by.get_full_name", read_only=True
    )
    updated_by = serializers.CharField(
        source="updated_by.get_full_name", read_only=True
    )
    created_on = serializers.DateTimeField(read_only=True, format="%Y-%m-%dT%H:%M:%S%z")
    updated_on = serializers.DateTimeField(read_only=True, format="%Y-%m-%dT%H:%M:%S%z")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Check if the model actually has the audit fields
        model = self.Meta.model
        audit_fields = ["created_by", "updated_by", "created_on", "updated_on"]

        for field_name in audit_fields:
            if not hasattr(model, field_name):
                # Dynamically pop the field out if the model doesn't support it
                self.fields.pop(field_name, None)

    def to_representation(self, instance):
        """remove empty audit data from being returned"""
        data = super().to_representation(instance)

        if data.get("updated_on") is None:
            data.pop("updated_on", None)

        if data.get("updated_by") is None:
            data.pop("updated_by", None)

        return data


# class GeneralAuditFieldsMixin(serializers.ModelSerializer):
#     """ Enterprise mixin to handle ownership and YES/NO formatting. """
#     created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
#     updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
#
#     def to_representation(self, instance):
#         """Automatically converts booleans to YES/NO for any field starting with 'is_'"""
#         data = super().to_representation(instance)
#         for field, value in data.items():
#             if field.startswith('is_') and isinstance(value, bool):
#                 data[field] = "YES" if value else "NO"
#         return data
#
#     def create(self, validated_data):
#         validated_data['created_by'] = self.context['request'].user
#         return super().create(validated_data)
#
#     def update(self, instance, validated_data):
#         validated_data['updated_by'] = self.context['request'].user
#         validated_data['updated_on'] = now_iso
#         return super().update(instance, validated_data)
