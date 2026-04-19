import random
import secrets
import string

from django.contrib.auth.password_validation import validate_password
from django.core.validators import EmailValidator
from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from phonenumber_field.phonenumber import to_python
from rest_framework import status
from rest_framework.response import Response
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator

from core import models


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


def mask_email(email: str) -> str:
    """
    Mask the local part of the email, leaving first 2 characters and domain visible.
    Example: username@gmail.com -> us*****@gmail.com
    """
    try:
        local, domain = email.split("@")
        if len(local) <= 2:
            masked_local = local[0] + "*" * (len(local) - 1)
        else:
            masked_local = local[:2] + "*" * (len(local) - 2)
        return f"{masked_local}@{domain}"
    except ValueError:
        return email


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


def get_greeting_name(user_instance):
    """ Always return the employee number linked to the user."""
    if hasattr(user_instance, "employee_profile") and user_instance.employee_profile.employee_number:
        return user_instance.employee_profile.employee_number.upper()
    return _("Staff Member")


def generate_new_otp(identifier: str, token_type: str):
    """
    Generates a OTP for user and sends it via SMS or Email.
    Otp.generate_new_code deletes existing unused codes and create a new one.

    Args:
        phone_number or email (str): The user's phone number or email (identifier).
        token_type (str): The current token_type.
    """
    # Normalize identifier to check for valid phone number format
    phone = to_python(identifier)

    try:
        query = Q(email__iexact=identifier)
        if phone and phone.is_valid():
            query |= Q(phone_number=phone)

        if token_type == models.Otp.TOKEN_TYPE_REGISTRATION:
            user = models.User.objects.get(query)
        else:
            user = models.User.objects.get(query, is_verified=True)

    except User.DoesNotExist:
        return Response(
            {"error": "No active count found with the given identifier."},
            status=status.HTTP_404_NOT_FOUND,
        )

    otp_entry = models.Otp.generate_new_code(user, token_type)

    # Route notification based on the identifier type provided
    if "@" in identifier:
        success, message = send_otp_email(otp_entry)
    else:
        # Fallback to email if SMS logic is not fully routed, or call send_sms
        success, message = send_otp_email(otp_entry)

    if not success:
        return Response(
            {"error": "Notification system error.", "detail": message},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    if token_type == models.Otp.TOKEN_TYPE_REGISTRATION:
        message = "OTP for account activation sent."
    elif token_type == models.Otp.TOKEN_TYPE_PASSWORD_RESET:
        message = "OTP for password reset sent."
    else:
        message = "OTP code sent! Check your Email/Phone."

    return Response({"message": message}, status=status.HTTP_200_OK)


def verify_otp(identifier: str, code: str, token_type: str):
    """
    Verifies OTP for the given phone number or email using the stored code, expiry, and usage status.
    it Finds the most recently created, unused OTP matching phone or email and type

    Args:
        phone_number (str): The phone number or email associated with the OTP.
        code (str): The OTP code to verify.
        token_type (str): The current token_type being validated.

    Returns:
        Response: DRF Response object indicating success or failure.
    """

    error = "Invalid or expired OTP code."
    error_message = {"error": error}

    # Normalize identifier for lookup
    phone = to_python(identifier)

    try:
        # Find user by email or phone to ensure correct UUID is obtained for OTP filter
        user = models.User.objects.get(Q(email__iexact=identifier) | Q(phone_number=phone))

        otp_entry = models.Otp.objects.filter(
            user=user, token_type=token_type, is_used=False
        ).latest("created_at")

    except (models.User.DoesNotExist, models.Otp.DoesNotExist):
        return Response(error_message, status=status.HTTP_400_BAD_REQUEST)

    if otp_entry.code != code:
        return Response(error_message, status=status.HTTP_400_BAD_REQUEST)

    if otp_entry.expires_at < timezone.now():
        otp_entry.is_used = True
        otp_entry.save()
        return Response(error_message, status=status.HTTP_400_BAD_REQUEST)

    if token_type == models.Otp.TOKEN_TYPE_REGISTRATION:
        user.is_verified = True
        user.save()
        message = "Account activated successfully."

    elif token_type == models.Otp.TOKEN_TYPE_PASSWORD_RESET:
        message = "OTP verified. Proceed to password change."

    else:
        message = "Login OTP verified."

    otp_entry.is_used = True
    otp_entry.save()

    return Response({"message": message}, status=status.HTTP_200_OK)


def send_otp_email(otp_entry: 'core.Otp'):
    """Sends a templated OTP email."""
    try:
        recipient_email = otp_entry.user.email
        context = {
            "greeting": f"Habari {otp_entry.user.get_full_name() or ''}".strip(),
            "otp_code": otp_entry.code,
            "token_type": otp_entry.token_type,
            "expiration_min": settings.OTP_EXPIRATION_TIME // 60,
        }

        html_content = render_to_string("emails/otp_email.html", context)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            f"Verification Code: {otp_entry.code} - Daz Electronics",
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        return True, "OTP sent successfully."

    except Exception as e:
        return handle_mail_exception(e)


def send_forgot_password_link_email(user, reset_link):
    """
    Sends a high-priority HTML email with a password reset link.
    """
    try:
        recipient_email = user.email

        context = {
            "greeting": f"Habari {user.get_full_name() or 'Mteja'}",
            "reset_link": reset_link,
            "frontend_url": settings.FRONTEND_URL,
        }

        html_content = render_to_string("emails/password_reset.html", context)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            "Reset Your Password - Daz Electronics",
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
        )
        email.attach_alternative(html_content, "text/html")

        email.extra_headers = {"X-Priority": "1 (Highest)", "Importance": "High"}

        email.send(fail_silently=False)
        print(f"Password Reset Link sent to {recipient_email}")
        return True, "Reset link sent successfully."

    except Exception as e:
        return handle_mail_exception(e)


def onboarding_email_to_staff(user_instance, password, completion_link=None, greeting_name = None):
    """
    Sends templated login credentials and setup link to new staff.
    Supports both Email and Phone as the primary identifier (username).
    """
    try:
        username = user_instance.email or str(user_instance.phone_number)

        context = {
            "greeting": _("Dear {name}").format(name=greeting_name),
            "login_url": f"{settings.FRONTEND_URL}/login",
            "setup_url": completion_link,
            "username": username,
            "password": password,
            "is_default_password": user_instance.is_default_password,
            "company_name": "Daz Electronics",
        }

        html_content = render_to_string("emails/staff_welcome.html", context)
        text_content = strip_tags(html_content)

        subject = _("Welcome to Daz Electronics - Your Staff Account is Ready")

        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user_instance.email],
        )
        email.attach_alternative(html_content, "text/html")

        email.send(fail_silently=False)

        return True, _("Staff credentials sent successfully to {email}").format(email=user_instance.email)

    except Exception as e:
        return handle_mail_exception(e)


def email_daily_closure_to_ceo(report_data, report_date):
    """Sends a single master report containing all agents' summaries to the CEO."""
    try:
        ceo_user = User.objects.filter(
            groups__name="Chief Executive Officer (CEO)"
        ).first()
        ceo_email = ceo_user.email if ceo_user else settings.ADMIN_EMAIL

        context = {
            "reports": report_data,
            "date": report_date,
            "total_company_revenue": sum(item["revenue"] for item in report_data),
            "total_cash_expected": sum(item["cash_on_hand"] for item in report_data),
            "total_momo_expected": sum(item["momo_collected"] for item in report_data),
            "total_expenses_expected": sum(
                item["total_expenses"] for item in report_data
            ),
            "frontend_url": settings.FRONTEND_URL,
        }

        html_content = render_to_string("emails/master_closure.html", context)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            f"MASTER Daily Sales Report - {report_date}",
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [ceo_email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        return True, "Master report delivered to CEO."

    except Exception as e:
        return handle_mail_exception(e)


def send_onboarding_notification(user, raw_password):
    """Dispatches the credentials via Email or SMS."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    greeting_name = get_greeting_name(user)

    frontend_base = settings.FRONTEND_URL.rstrip("/")
    completion_link = f"{frontend_base}/setup-account/{uid}/{token}/"

    if user.email:
        return onboarding_email_to_staff(
            user_instance=user,
            password=raw_password,
            completion_link=completion_link,
            greeting_name=greeting_name,
        )

    elif user.phone_number:
        sms_text = (
            f"Karibu! Your staff account is ready. "
            f"Username: {user.phone_number} "
            f"Password: {raw_password}. "
            f"Login here: {completion_link}"
        )
        return send_sms(user.phone_number, sms_text)

    return False, "No valid email or phone number found to notify."


def universal_path_generator(instance, filename, folder_base, name_attr="name"):
    """
    Handles path generation for any model.
    - folder_base: e.g., 'Electronics/Images'
    - name_attr: The attribute on the instance to use for slugifying
    """
    ext = filename.split(".")[-1]

    raw_name = "generic"

    for attr in [
        name_attr,
        "product.name",
        "user.get_full_name",
        "owner.get_full_name",
    ]:
        try:
            val = instance
            for part in attr.split("."):
                val = getattr(val, part)
                if callable(val):
                    val = val()
            raw_name = val
            break
        except AttributeError:
            continue

    unique_id = uuid.uuid4().hex[:8]
    clean_name = f"{slugify(raw_name)}_{unique_id}.{ext}"
    return os.path.join(f"Media/{folder_base}", clean_name)

def upload_profile_picture(inst, fn):
    return universal_path_generator(inst, fn, "Profile")


def upload_personal_id(inst, fn):
    return universal_path_generator(inst, fn, "IDs")


def upload_employee_contract_document(inst, fn):
    return universal_path_generator(inst, fn, "Contracts/Employees")


def upload_tenant_contract_document(inst, fn):
    return universal_path_generator(inst, fn, "Contracts/Tenants")


def upload_product_image(inst, fn):
    return universal_path_generator(inst, fn, "Electronics/Images")


def upload_product_video(inst, fn):
    return universal_path_generator(inst, fn, "Electronics/Videos")


def upload_software_image(inst, fn):
    return universal_path_generator(inst, fn, "Software/Images")
