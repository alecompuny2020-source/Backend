"""
CHOICES AND CONSTANTS REGISTRY FOR AN ENTERPRISE

This file serves as the central source of truth for all standardized choices,
lookups, and configuration constants used across the Enterprise System

Responsibility:
- Maintain consistency in database values.
- Provide human-readable, translatable labels for the UI.
- Define application-wide configuration (OTP, Token Types).
"""

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

now = timezone.now
now_iso = timezone.now().isoformat()
current_time = timezone.now()

OTP_CODE_LENGTH = getattr(settings, "OTP_CODE_LENGTH", 6)
OTP_EXPIRATION_TIME_MINUTES = getattr(settings, "OTP_EXPIRATION_TIME_MINUTES", 5)


class TokenType(models.TextChoices):
    REGISTRATION = "REGISTRATION", _("Registration")
    LOGIN = "LOGIN", _("Login")
    PASSWORD_RESET = "PASSWORD_RESET", _("Password Reset")
    TRANSACTION_AUTH = "TRANSACTION_AUTH", _("Transaction Authorization")
    EMAIL_CHANGE = "EMAIL_CHANGE", _("Email Change Verification")
    PHONE_VERIFICATION = "PHONE_VERIFICATION", _("Phone Number Verification")
    TwoFA_ENABLE = "2FA_ENABLE", _("Two-Factor Auth Enablement")
    ACCOUNT_DELETION = "ACCOUNT_DELETION", _("Account Deletion Confirmation")
    STAFF_INVITATION = "STAFF_INVITATION", _("Staff Onboarding Invitation")


class CommunicationMethod(models.TextChoices):
    EMAIL = "email", _("Email")
    PHONE = "phone", _("Phone")
    BOTH = "both", _("Both")


class LanguageChoice(models.TextChoices):
    EN_US = "en-us", _("English (US)")
    EN_GB = "en-gb", _("English (British)")
    SW = "sw", _("Kiswahili")


class Gender(models.TextChoices):
    MALE = "MALE", _("Male")
    FEMALE = "FEMALE", _("Female")
    OTHER = "OTHER", _("Other")
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY", _("Prefer Not to Say")


class MaritalStatus(models.TextChoices):
    SINGLE = "SINGLE", _("Single")
    MARRIED = "MARRIED", _("Married")
    DIVORCED = "DIVORCED", _("Divorced")


class RecipientType(models.IntegerChoices):
    USER = 0, _("User")
    GROUP = 1, _("Group")
    BROADCAST = 2, _("Broadcast")
    AGENT = 3, _("Agent")
