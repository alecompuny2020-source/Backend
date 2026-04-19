""" Constitutes shared resources to make Enterprise code DRY """

from django.contrib.auth.password_validation import validate_password
from django.core.validators import EmailValidator
from phonenumber_field.phonenumber import to_python


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


def generate_secure_password(length=12):
    """
    Generates a cryptographically secure, random password for new staff.
    Shuffles the characters for better security and returns the plaintext string.
    """
    if length < 8:
        raise ValueError(
            "Password length must be at least 8 to include all required character types."
        )

    chars = string.ascii_letters + string.digits + string.punctuation

    lower = string.ascii_lowercase
    upper = string.ascii_uppercase
    digits = string.digits
    symbols = string.punctuation

    password_list = [
        secrets.choice(lower),
        secrets.choice(upper),
        secrets.choice(digits),
        secrets.choice(symbols),
    ]

    remaining_length = length - len(password_list)

    password_list.extend(secrets.choice(chars) for _ in range(remaining_length))

    random.SystemRandom().shuffle(password_list)

    plaintext_password = "".join(password_list)
    print(plaintext_password)

    return plaintext_password


def mask_email(email: str) -> str:
    """
    Mask the local part of the email, leaving first 2 and last 1 characters visible.
    Example: username@gmail.com -> us*****e@gmail.com
    """
    try:
        local, domain = email.split("@")

        if len(local) <= 3:
            masked_local = local[0] + "*" * (len(local) - 2) + local[-1] if len(local) > 1 else local + "*"
        else:
            masked_local = local[:2] + "*" * (len(local) - 3) + local[-1]

        return f"{masked_local}@{domain}"
    except ValueError:
        return email

def mask_phone(phone: str) -> str:
    """
    Mask phone number
    Example: +255692012343 -> +255******343
    """
    phone_str = str(phone)
    if len(phone_str) > 6:
        return f"{phone_str[:4]}******{phone_str[-3:]}"
    return phone_str

def get_greeting_name(user_instance):
    """ Always return the employee number linked to the user."""
    if hasattr(user_instance, "employee_profile") and user_instance.employee_profile.employee_number:
        return user_instance.employee_profile.employee_number.upper()
    return _("Staff Member")
