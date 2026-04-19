import logging
import socket
from http import HTTPStatus
from smtplib import SMTPAuthenticationError, SMTPConnectError, SMTPException
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import ProtectedError, RestrictedError
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def format_error_payload(status_code, message, details):
    """Helper to maintain the Enterprise Response Envelope structure."""
    return {
        "success": False,
        "error": {
            "status_code": status_code,
            "message": message,
            "details": details,
        },
    }


def handle_mail_exception(e):
    """
    Categorizes errors into user-friendly messages
    while logging the technical details for debugging.
    """

    logger.error(f"Email system error: {str(e)}")
    print(f"DEBUG: Technical Email Error -> {e}")

    if isinstance(e, (socket.gaierror, socket.timeout, TimeoutError, SMTPConnectError)):
        return (
            False,
            "Network error or timeout. Please check your internet connection and try again.",
        )

    if isinstance(e, SMTPAuthenticationError):
        return (
            False,
            "Email service is temporarily unavailable. Please contact support if this persists.",
        )

    if isinstance(e, SMTPException):
        return (
            False,
            "We couldn't deliver the email. Please double-check the address or try again.",
        )

    return (
        False,
        "Oops, something went wrong while sending the email. Please try again.",
    )


def general_exception_handler(exc: Exception, context: dict[str, Any]) -> Response:
    """
    Custom API exception handler for:
    1. Mapping Django Validation errors to DRF format.
    2. Handling Database ProtectedError & RestrictedError.
    3. Wrapping all errors in a standardized 'error' JSON envelope.
    """

    # Converts Django's internal Model.clean() ValidationErrors into DRF format
    if isinstance(exc, DjangoValidationError):
        from rest_framework.serializers import as_serializer_error
        exc = DRFValidationError(as_serializer_error(exc))

    # Handles Foreign Key restrictions (Protect and Restrict)
    if isinstance(exc, (ProtectedError, RestrictedError)):
        blocking_objects = (
            exc.protected_objects if isinstance(exc, ProtectedError)
            else exc.restricted_objects
        )

        blocking_models = {
            obj._meta.verbose_name.title() for obj in blocking_objects
        }
        model_list = ", ".join(blocking_models)

        error_message = f"Cannot delete: This item is used in {model_list}. Try deactivating it instead."

        return Response(
            format_error_payload(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Database Restriction",
                details=error_msg
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    # Calls DRF's default exception handler for other errors
    response = drf_exception_handler(exc, context)

    # Standardized wrapping for all other errors
    if response is not None:
        http_code_to_message = {v.value: v.phrase for v in HTTPStatus}

        status_msg = http_code_to_message.get(
            response.status_code,
            # "An unexpected error occurred",
            "Oops something went wrong, Please try again later...!",
        )

        # Wraps everything in the standardized envelope
        response.data = format_error_payload(
            status_code=response.status_code,
            message=status_msg,
            details=response.data
        )

    return response
