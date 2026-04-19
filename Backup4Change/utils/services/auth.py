from django.db.models import Q
from rest_framework.exceptions import NotFound, APIException
from django.utils.translation import gettext_lazy as _
from phonenumber_field.phonenumber import to_python

def initiate_user_login_otp(identifier):
    """
    Business logic for finding a user and sending a login OTP.
    """
    phone_number = to_python(identifier)

    # 1. User Lookup (matches your custom auth backend logic)
    try:
        user = User.objects.get(
            Q(email__iexact=identifier) | Q(phone_number=phone_number)
        )
    except User.DoesNotExist:
        # Enterprise Tip: Use generic messages to prevent user enumeration
        raise NotFound(_("No active account found with those credentials."))

    # 2. OTP Generation
    otp_entry = Otp.generate_new_code(user, Otp.TOKEN_TYPE_LOGIN)

    # 3. Notification Routing
    # We prioritize email if an email identifier was used, otherwise SMS
    if user.email and "@" in identifier:
        success, message = send_otp_email(otp_entry)
    else:
        # success, message = send_otp_sms(otp_entry)
        success, message = send_otp_email(otp_entry)

    if not success:
        # This will be caught by your general_exception_handler
        raise APIException(message)

    return user
