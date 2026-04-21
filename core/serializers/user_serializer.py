from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed as af
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from phonenumber_field.phonenumber import to_python
from common.choices import (TOKEN_TYPE_REGISTRATION)
from common.utils import (enforce_password, validate_user_identifier)
from common.managers import EnterpriseOTPandLinkManager as OTPManager
from core.models import User, Otp
from django.db.models import Q
import base64
import json



class RegistrationSerializer(serializers.ModelSerializer):
    """Performs self-user registration (for customers) and generates the initial OTP."""

    identifier = serializers.CharField()

    class Meta:
        model = User
        fields = ["identifier", "password", "first_name", "last_name"]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        first_name = attrs.get("first_name", "").strip()
        last_name = attrs.get("last_name", "").strip()

        if not identifier:
            raise serializers.ValidationError(
                {"identifier": _("Either a valid email or phone number must be provided.")}
            )

        if not first_name or not last_name:
            raise serializers.ValidationError(
                {"names": _("Both first name and last name are required.")}
            )

        if not first_name.isalpha() or not last_name.isalpha():
            raise serializers.ValidationError(
                {"names": _("Names must contain only letters.")}
            )

        return attrs

    def validate_password(self, value):
        """Enforces password Policy"""
        return enforce_password(value)

    def validate_identifier(self, value):
        """Ensure identifier is a valid email or phone number."""
        return validate_user_identifier(value)

    def create(self, validated_data):
        """Perform create and trigger the new OTP Manager logic."""
        identifier = validated_data.pop("identifier")
        password = validated_data.pop("password")

        # Determine identifier type
        email = identifier if "@" in identifier else None
        phone_number = to_python(identifier) if not email else None

        user = User.objects.create_user(
            email=email,
            phone_number=phone_number,
            password=password,
            **validated_data
        )

        try:
            otp_entry = OTPManager.generate_and_send(
                identifier=identifier,
                token_type=TOKEN_TYPE_REGISTRATION,
            )

        except Exception as e:
            user.delete()
            raise serializers.ValidationError({"otp_error": str(e)})

        return user


class ConfirmRegistrationSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    OTP = serializers.CharField(max_length=6)

    def validate_identifier(self, value):
        """Ensure identifier is a valid email or phone number."""
        return validate_user_identifier(value)


class RequestLoginOTPSerializer(serializers.Serializer):
    """Step 1 of 2FA: Accept either email or phone and send OTP."""

    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate_identifier(self, value):
        """Ensure identifier is a valid email or phone number."""
        return validate_user_identifier(value)

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        password = attrs.get("password")

        # authenticate() uses EnterpriseEmailOrPhoneAuthBackend automatically
        user = authenticate(username=identifier, password=password)

        if not getattr(user, "is_verified", True):
            raise af(_("Account not yet verified. Please verify your identity."))

        if not user:
            raise af(_("No active account found with the given credentials."))
            # raise af("User inactive or deleted.")

        attrs["user"] = user
        return attrs


class LoginConfirmOTPSerializer(serializers.Serializer):
    """Step 2 of 2FA: Verify OTP against the user identified by email or phone number."""

    identifier = serializers.CharField()
    OTP = serializers.CharField(max_length=6)

    def validate_identifier(self, value):
        """Ensure identifier is a valid email or phone number."""
        return validate_user_identifier(value)


class UserDetailsSerializer(serializers.ModelSerializer):
    """Used to safely serialize the user object for 'user_data' JWT field."""

    groups = serializers.SerializerMethodField()
    preferred_language = serializers.SerializerMethodField()
    preferred_currency = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "phone_number", "first_name", "last_name", "email", "is_verified",
            "is_default_password", "groups", "is_profile_complete",
            "preferred_language", "preferred_currency"
        ]

    def get_groups(self, obj):
        """ Returns a list of group names user belongs to. """
        return list(obj.groups.values_list("name", flat=True))

    def get_preferred_language(self, obj):
        """Extracts language from the linked UserPreference JSONField"""
        user_prefs = getattr(obj, 'preferences', None)
        if user_prefs and user_prefs.preferences:
            return user_prefs.preferences.get('preferred_language', 'en-us')
        return 'en-us'

    def get_preferred_currency(self, obj):
        """Extracts currency from the linked UserPreference JSONField"""
        user_prefs = getattr(obj, 'preferences', None)
        if user_prefs and user_prefs.preferences:
            return user_prefs.preferences.get('preferred_currency', 'TZS')
        return 'TZS'


class UserTokenObtainPairSerializer(TokenObtainPairSerializer):
    """SimpleJWT Serializer for direct login or post-OTP token issuance."""

    # SimpleJWT defaults to 'username'. now it set to flexible.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field] = serializers.CharField()

    def get_user_data(self, user):
        user_data = UserDetailsSerializer(user).data
        user_data_json = json.dumps({"user": user_data})
        return base64.urlsafe_b64encode(user_data_json.encode("utf-8")).decode("utf-8")

    def validate(self, attrs):
        # attrs[self.username_field] holds the email or phone number
        identifier = attrs.get(self.username_field)
        password = attrs.get("password")

        user = authenticate(username=identifier, password=password)

        if not user or not user.is_active:
            raise af(_("No active account found with the given credentials."))

        refresh = self.get_token(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user_data": self.get_user_data(user),
        }


class BaseIdentifierSerializer(serializers.Serializer):
    """Base class to provide shared identifier validation logic."""
    identifier = serializers.CharField()

    def validate_identifier(self, value):
        """Standardized validation for both email and phone numbers."""
        value = validate_user_identifier(value)
        phone = to_python(value) if "@" not in value else None

        user = User.objects.filter(
            Q(email__iexact=value) | Q(phone_number=phone)
        ).exists()

        if not user:
            raise serializers.ValidationError(
                _("No active account found with the given credentials.")
            )

        return value


class RequestOTPSerializer(BaseIdentifierSerializer):
    """Initiates OTP sending by validating identifier existence."""
    pass


class ConfirmPasswordResetSerializer(serializers.Serializer):
    """
    Confirms password reset: Validates OTP and sets the new password.
    Requires OTP code and new password.
    """

    identifier = serializers.CharField()
    OTP = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        """Enforces password Policy"""
        return enforce_password(value)

    def validate_identifier(self, value):
        """Ensures identifier is a valid email or phone number."""
        return validate_user_identifier(value)

    def validate(self, attrs):
        otp_response = OTPManager.verify(
            attrs["identifier"],
            attrs["OTP"],
            Otp.TOKEN_TYPE_PASSWORD_RESET
        )

        if otp_response.status_code != status.HTTP_200_OK:
            raise serializers.ValidationError(otp_response.data)

        # Fetchs and attachs the user so save() can use it
        phone = to_python(attrs["identifier"])
        try:
            attrs["user"] = User.objects.get(
                Q(email__iexact=attrs["identifier"]) | Q(phone_number=phone)
            )
        except User.DoesNotExist:
            raise serializers.ValidationError(
                _("No active account found with the given credentials.")
            )

        return attrs

    def save(self):
        """Logic to actually change the password."""
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.is_default_password = False
        user.save()
        return user


class RequestForgotPasswordSerializer(BaseIdentifierSerializer):
    """Initiates password reset using identifier validation."""
    pass


class ConfirmForgotPasswordSerializer(serializers.Serializer):
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
