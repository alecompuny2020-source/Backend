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
