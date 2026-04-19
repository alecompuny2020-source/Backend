import base64
import json
import random
import secrets
import string

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError as ve
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from phonenumber_field.phonenumber import to_python
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers, status
from rest_framework.exceptions import AuthenticationFailed as af
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.translation import gettext_lazy as _
from utils.services import (enforce_password, validate_user_identifier, generate_secure_password,
                          send_otp_email, send_onboarding_notification, onboarding_email_to_staff)

from .models import Otp, UserAddress, UserPreference
from hrms.models import Department, Employee, NextOfKin, UserIdentity
from lrh.models import EmployeeRegistrationHistory
from hrms.serializers import NextOfKinSerializer, UserIdentitySerializer
from utils.choices import EMPLOYMENT_TYPES

User = get_user_model()


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
        first_name = attrs.get("first_name")
        last_name = attrs.get("last_name")

        if not identifier:
            raise serializers.ValidationError(
                {"identifier": _("Either a valid email or phone number must be provided.")}
            )

        if not first_name or not last_name:
            raise serializers.ValidationError(
                {"names": _("Both first name and last name are required.")}
            )

        if not first_name or not first_name.strip():
            raise serializers.ValidationError({"first_name": _("First name cannot be empty.")})
        if not last_name or not last_name.strip():
            raise serializers.ValidationError({"last_name": _("Last name cannot be empty.")})

        if not first_name.isalpha():
            raise serializers.ValidationError({"first_name": _("First name must contain only letters.")})
        if not last_name.isalpha():
            raise serializers.ValidationError({"last_name": _("Last name must contain only letters.")})

        return attrs


    def to_internal_value(self, data):
        """
        Converts the incoming empty string for either 'email' or 'phone number' to None (NULL in DB)
        to ensure the unique constraint is not violated by duplicate empty strings.
        """

        internal_value = super().to_internal_value(data)

        if "phone_number" in internal_value and internal_value["phone_number"] == "":
            internal_value["phone_number"] = None

        if "email" in internal_value and internal_value["email"] == "":
            internal_value["email"] = None

        return internal_value

    def validate_password(self, value):
        """Enforces password Policy"""
        return enforce_password(value)

    def validate_identifier(self, value):
        """Ensure identifier is a valid email or phone number."""
        return validate_user_identifier(value)

    def create(self, validated_data):
        """ Perform create as per provided identifier """
        identifier = validated_data.pop("identifier", None)
        password = validated_data.pop("password", None)
        email = validated_data.pop("email", None)
        phone_number = validated_data.pop("phone_number", None)

        email = identifier if "@" in identifier else None
        phone_number = to_python(identifier) if not email else None

        user = User.objects.create_user(
            email=email,
            phone_number=phone_number,
            password=password,
            **validated_data
        )

        otp_entry = Otp.generate_new_code(user, Otp.TOKEN_TYPE_REGISTRATION)

        if user.email:
            success, message = send_otp_email(otp_entry)
            if not success:
                user.delete()
                raise serializers.ValidationError({"email_error": message})
        # elif user.phone_number:
        #     success, message = send_otp_sms(otp_entry)
        #     if not success:
        #         user.delete()
        #         raise serializers.ValidationError({"phone_error": message})

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

        # authenticate() will use EmailOrPhoneAuthentication automatically
        user = authenticate(username=identifier, password=password)

        if not user or not user.is_active:
            raise af(_("No active account found with the given credentials."))
            # raise af("User inactive or deleted.")

        if not getattr(user, "is_verified", True):
            raise af(_("Account not yet verified. Please verify your identity."))

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

    """ The possibiblity where all staff will use their own serializer rather
        that customers who will also use their individual serializer for data safety
    """

    groups = serializers.SerializerMethodField()
    preferred_language = serializers.SerializerMethodField()
    preferred_currency = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "phone_number",
            "first_name",
            "last_name",
            "email",
            "is_verified",
            "is_default_password",
            "groups",
            "is_profile_complete",
            "preferred_language",
            "preferred_currency"
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


class RequestForgotPasswordSerializer(serializers.Serializer):
    """Initiates password reset using either identifier."""

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


class RequestOTPSerializer(serializers.Serializer):
    """Initiates password reset by sending an OTP to either phone number or email."""

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


class ConfirmPasswordResetSerializer(serializers.Serializer):
    """
    Confirms password reset: Validates OTP and sets the new password.
    Requires OTP code and new password.
    """

    identifier = serializers.CharField()
    OTP = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        return enforce_password(value)

    def validate_identifier(self, value):
        """Ensure identifier is a valid email or phone number."""
        return validate_user_identifier(value)


class ProfilePictureSerializer(serializers.ModelSerializer):
    """ For user profile picture management """
    class Meta:
        model = User
        fields = ["profile_picture"]


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = [
            "id", "address_type", "is_default",
            "street_address", "city", "state_province",
            "postal_code", "country"
        ]


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = ["preferences"]


class StaffOnboardingSerializer(serializers.Serializer):
    identifier = serializers.CharField(help_text=_("Email or Phone Number"))
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all())
    employment_type = serializers.ChoiceField(choices=EMPLOYMENT_TYPES)
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), required=False)
    remarks = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if not attrs.get("identifier"):
            raise serializers.ValidationError(
                _("Either a valid email or phone number must be provided.")
            )
        return attrs

    def validate_identifier(self, value):
        """Ensure identifier is a valid email or phone number."""
        return validate_user_identifier(value)

    @transaction.atomic
    def create(self, validated_data):
        identifier = validated_data['identifier']
        department = validated_data['department']
        emp_type = validated_data['employment_type']
        remarks = validated_data.get('remarks', "Initial system onboarding.")
        group = validated_data.get('group')
        request = self.context.get('request')

        email = identifier if "@" in identifier else None
        phone_number = to_python(identifier) if not email else None

        raw_password = generate_secure_password()
        year = timezone.now().year
        prefix = f"EMP-{year}"
        last_emp = Employee.objects.filter(employee_number__startswith=prefix).order_by("-employee_number").first()
        if last_emp:
            last_count = int(last_emp.employee_number.split('-')[-1])
            new_count = last_count + 1
        else:
            new_count = 1

        new_emp_number = f"{prefix}-{new_count:04d}"

        user = User.objects.create_user(
            email=email,
            phone_number=phone_number,
            password=raw_password,
            is_staff=True,
            is_active=True,
            is_default_password=True
        )

        if group:
            user.groups.add(group)

        # Create Employee Profile
        employee = Employee.objects.create(
            user=user,
            department=department,
            employment_type=emp_type,
            employee_number=new_emp_number,
            hire_date=timezone.now().date(),
            base_salary = 0
        )

        # Initialize Registration Audit History
        EmployeeRegistrationHistory.objects.create(
            employee=employee,
            status="PENDING",
            remarks=remarks,
            initiated_by=request.user if request and request.user.is_authenticated else None
        )

        user.status_metadata = self._build_initial_metadata(request, email, new_emp_number)
        user.save(update_fields=['status_metadata'])

        user.status_metadata = metadata
        user.save()

        success, message = send_onboarding_notification(user, raw_password)

        if not success:
            user.status_metadata["onboarding"]["notification_status"] = "FAILED"
            user.status_metadata["onboarding"]["error_log"] = message
            user.save(update_fields=['status_metadata'])

            raise serializers.ValidationError({
                "notification_error": _("Onboarding failed: ") + message
            })

        else:
            user.status_metadata["onboarding"]["notification_status"] = "SUCCESS"
            user.save(update_fields=['status_metadata'])

        return employee

    def _build_initial_metadata(self, request, email, emp_no):
        """Helper to keep the create method clean and reserve metadata."""

        now_iso = timezone.now().isoformat()

        return {
            "onboarding": {
                "initiator_ip": request.META.get("REMOTE_ADDR") if request else None,
                "method": "Email" if email else "SMS",
                "notification_status": "PENDING",
            },
            "password_history": [
                {
                    "timestamp": timezone.now().isoformat(),
                    "password_generated": True,
                    "reason": "Initial Onboarding"
                }
            ],
            "profile_completion_checklist": {
                "identity_uploaded": False,
                "emergency_contact_added": False,
                "bank_details_provided": False,
                "education_details_provided": False
            },
            "security_log": {
                "last_password_change": timezone.now().isoformat(),
                "is_forced_reset_pending": False
            }
        }


class OnboardConfirmSerializer(serializers.Serializer):
    """ Serializer for confirming staff onboarding via secure link."""
    uid = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only = True)

    def validate(self, attrs):
        uid = attrs.get("uid")
        token = attrs.get("token")

        if not uid or not token:
            raise serializers.ValidationError(
                {"detail": _("Both UID and token are required.")}
            )

        return attrs

    def validate_new_password(self, value):
        """Enforces password Policy"""
        return enforce_password(value)


class RequestOnboardingLinkSerializer(serializers.Serializer):
    identifier = serializers.CharField()

    def validate_identifier(self, value):
        """Ensure identifier is a valid email or phone number."""

        value = validate_user_identifier(value)
        phone = to_python(value) if "@" not in value else None
        user = User.objects.filter(
            Q(email__iexact=value) | Q(phone_number=phone)
        ).first()

        if not user:
            raise serializers.ValidationError(
                _("No staff account found with the given credentials.")
            )

        if not user.is_default_password or user.is_verified:
            raise serializers.ValidationError({
                "error": _("This account is already fully activated. Please use the login or forgot password options.")
            })

        self.user = user
        return value



class CompleteProfileSerializer(serializers.ModelSerializer):
    """ Onboard profile completion serializer by the authenticated and qualified employee """
    personal_info = serializers.JSONField(write_only=True, required = True)
    residential_details = UserAddressSerializer(many=True)
    preferences = serializers.JSONField(write_only=True)
    contact_details = serializers.JSONField(write_only=True)
    financial_details = serializers.JSONField(write_only=True)
    next_of_kin = NextOfKinSerializer(many=True)
    identities = UserIdentitySerializer(many=True)

    class Meta:
        model = User
        fields = [
            'personal_info', 'residential_details', 'next_of_kin', 'identities',
            'preferences', 'contact_details', 'financial_details'
        ]

    def update(self, instance, validated_data):
        personal = validated_data.pop('personal_info', {})
        residential = validated_data.pop('residential_details', None)
        prefs = validated_data.pop('preferences', {})
        contacts = validated_data.pop('contact_details', {})
        financial = validated_data.pop('financial_details', {})
        nok_data = validated_data.pop('next_of_kin', None)
        user_identities = validated_data.pop('identities', None)

        with transaction.atomic():
            instance.first_name = personal.get('first_name', instance.first_name)
            instance.middle_name = personal.get('middle_name', instance.middle_name)
            instance.last_name = personal.get('last_name', instance.last_name)

            if hasattr(instance, 'employee_profile'):
                emp = instance.employee_profile
                emp.gender = personal.get('gender', emp.gender)
                emp.marital_status = personal.get('marital_status', emp.marital_status)
                emp.hr_metadata['religion'] = personal.get('religion', emp.hr_metadata.get('religion'))
                emp.save()

            if residential is not None:
                instance.addresses.all().delete()
                for addr in residential:
                    UserAddress.objects.create(user=instance, **addr)

            if prefs and hasattr(instance, 'preferences'):
                instance.preferences.preferences.update(prefs)
                instance.preferences.save()

            if hasattr(instance, 'employee_profile'):
                emp = instance.employee_profile
                emp.hr_metadata.update({
                    "secondary_phone": contacts.get("second_phone"),
                    "secondary_email": contacts.get("second_email")
                })
                emp.save()

            if financial and hasattr(instance, 'employee_profile'):
                emp = instance.employee_profile
                payroll = emp.hr_metadata.get('payroll_config', {})
                payroll.update({
                    "bank_name": financial.get("bank_type"),
                    "account_name": financial.get("account_name"),
                    "account_number": financial.get("account_number")
                })
                emp.hr_metadata['payroll_config'] = payroll
                emp.save()

            if nok_data is not None and hasattr(instance, 'employee_profile'):
                emp = instance.employee_profile
                emp.next_of_kin_contacts.all().delete()
                for nok in nok_data:
                    NextOfKin.objects.create(owner=emp, **nok)

            if user_identities is not None and hasattr(instance, 'employee_profile'):
                emp = instance.employee_profile
                emp.identities.all().delete()
                for identity in user_identities:
                    UserIdentity.objects.create(owner=emp, **identity)

            instance.is_profile_complete = True
            instance.save()
            return instance
