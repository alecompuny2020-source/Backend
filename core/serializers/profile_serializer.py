from rest_framework import serializers
from core.models import User, UserPreference, UserAddress



class UserPersonalInfoSerializer(serializers.ModelSerializer):
    """Handles core personal identity: Names and joining info."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            "first_name", "middle_name", "last_name",
            "full_name", "date_joined"
        ]
        read_only_fields = ["date_joined"]



class UserAccountStatusSerializer(serializers.ModelSerializer):
    """Provides a granular view of the user's verification and setup status."""
    class Meta:
        model = User
        fields = [
            "is_active", "is_verified", "is_staff",
            "is_profile_complete", "status_metadata"
        ]
        read_only_fields = fields



class UserContactInfoSerializer(serializers.ModelSerializer):
    """Handles Email and Phone Number management."""
    class Meta:
        model = User
        fields = ["email", "phone_number"]


class ProfilePictureSerializer(serializers.ModelSerializer):
    """ For user profile picture management """
    class Meta:
        model = User
        fields = ["profile_picture"]


class UserAddressSerializer(serializers.ModelSerializer):
    """ For user address management """
    class Meta:
        model = UserAddress
        fields = [
            "id", "address_type", "is_default",
            "street_address", "city", "state_province",
            "postal_code", "country"
        ]


class UserPreferenceSerializer(serializers.ModelSerializer):
    """ For user preference management """
    class Meta:
        model = UserPreference
        fields = ["preferences"]


class UserProfileDetailSerializer(serializers.ModelSerializer):
    """A comprehensive nested view of the entire user profile management."""
    personal_info = UserPersonalInfoSerializer(source='*', read_only=True)
    contact_info = UserContactInfoSerializer(source='*', read_only=True)
    status = UserAccountStatusSerializer(source='*', read_only=True)

    # Nested related models
    preferences = UserPreferenceSerializer(read_only=True)
    addresses = UserAddressSerializer(many=True, read_only=True, source='useraddress_set')
    profile_picture = ProfilePictureSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "personal_info", "contact_info",
            "status", "preferences", "addresses", "profile_picture"
        ]
