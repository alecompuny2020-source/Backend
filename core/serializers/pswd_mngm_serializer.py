from rest_framework import serializers
from common.utils import validate_user_identifier
from phonenumber_field.phonenumber import to_python
from core.models import User


class RequestForgotPasswordSerializer(serializers.Serializer):
    """Initiates password reset using either identifier(email or password)."""

    identifier = serializers.CharField()

    def validate_identifier(self, value):
        """Ensure identifier is a valid email or phone number."""

        value = validate_user_identifier(value)
        phone = to_python(value) if "@" not in value else None
        user_exists = User.objects.filter(
            Q(email__iexact=value) | Q(phone_number=phone)
        ).exists()

        if not user_exists:
            raise serializers.ValidationError(
                _("No active account found with the given credentials.")
            )

        return value


class ForgotPasswordConfirmSerializer(serializers.Serializer):
    """confirm forgot password reset using either identifier."""

    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    uid = serializers.CharField()
    token = serializers.CharField()

    def validate_new_password(self, value):
        """Enforcess password Policy"""
        return enforce_password(value)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(_("Passwords do not match."))

        return attrs
