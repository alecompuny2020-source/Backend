def enforce_password(value):
    """Enforces Django's configured password policy."""
    try:
        validate_password(value)
    except ve as e:
        raise serializers.ValidationError(e.messages)
    return value

def validate_user_identifier(value):
    """Ensures identifier is a valid email or phone number."""
    if "@" in value:
        EmailValidator()(value)
    else:
        to_python(value)
    return value
