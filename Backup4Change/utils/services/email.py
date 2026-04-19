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
