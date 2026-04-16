from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .exceptions import handle_mail_exception

class EmailSenderService:
    """Handles all outgoing email notifications using templated HTML content."""

    @staticmethod
    def _send_multipart_email(subject, recipient, template, context, high_priority=False):
        """Internal helper to dispatch HTML emails with a plain-text fallback."""
        try:
            html_content = render_to_string(template, context)
            text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject, text_content, settings.DEFAULT_FROM_EMAIL, [recipient]
            )
            email.attach_alternative(html_content, "text/html")

            if high_priority:
                email.extra_headers = {"X-Priority": "1 (Highest)", "Importance": "High"}

            email.send(fail_silently=False)
            return True, "Email sent successfully."
        except Exception as e:
            return handle_mail_exception(e)

    @classmethod
    def send_otp(cls, otp_entry):
        """Sends an OTP email with bilingual greeting logic."""
        user = otp_entry.user
        greeting = f"Habari {user.get_full_name() or ''}".strip()

        context = {
            "greeting": greeting,
            "otp_code": otp_entry.code,
            "token_type": otp_entry.token_type,
            "expiration_min": settings.OTP_EXPIRATION_TIME // 60,
        }
        return cls._send_multipart_email(
            subject=f"Verification Code: {otp_entry.code} - Daz Electronics",
            recipient=user.email,
            template="emails/otp_email.html",
            context=context
        )

    @classmethod
    def send_password_reset(cls, user, reset_link):
        """Sends a high-priority password reset link."""
        context = {
            "greeting": f"Habari {user.get_full_name() or 'Mteja'}",
            "reset_link": reset_link,
            "frontend_url": settings.FRONTEND_URL,
        }
        return cls._send_multipart_email(
            subject="Reset Your Password - Daz Electronics",
            recipient=user.email,
            template="emails/password_reset.html",
            context=context,
            high_priority=True
        )

    @classmethod
    def send_staff_onboarding(cls, user, password, completion_link, greeting_name):
        """Sends credentials to a new staff member's email."""
        context = {
            "greeting": f"Dear {greeting_name}",
            "login_url": f"{settings.FRONTEND_URL}/login",
            "setup_url": completion_link,
            "username": user.email,
            "password": password,
            "company_name": "Daz Electronics",
        }
        return cls._send_multipart_email(
            subject="Welcome to Daz Electronics - Your Staff Account is Ready",
            recipient=user.email,
            template="emails/staff_welcome.html",
            context=context
        )
