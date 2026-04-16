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

class APIExceptionHandler:
    """
    Enterprise Exception Handler.
    Manages the transformation and formatting of API exceptions.

    - Transform Django Validation Errors to DRF
    - Check for Database Restrictions (Protected/Restricted)
    - Use default DRF handler for standard errors (404, 401, etc.)
    - Apply the Enterprise Envelope for response similarity

    """

    def __init__(self, exc: Exception, context: dict[str, Any]):
        self.exc = exc
        self.context = context

    def handle(self) -> Response:
        self._normalize_validation_error()
        db_response = self._handle_db_restrictions()
        if db_response:
            return db_response

        response = drf_exception_handler(self.exc, self.context)

        if response is not None:
            return self._format_to_envelope(response)

        return response

    def _normalize_validation_error(self):
        """Converts Django's Model.clean() errors into DRF format."""
        if isinstance(self.exc, DjangoValidationError):
            self.exc = DRFValidationError(as_serializer_error(self.exc))

    def _handle_db_restrictions(self) -> Response | None:
        if isinstance(self.exc, (ProtectedError, RestrictedError)):
            blocking_objects = (
                self.exc.protected_objects if isinstance(self.exc, ProtectedError)
                else self.exc.restricted_objects
            )

            blocking_models = {
                obj._meta.verbose_name.title() for obj in blocking_objects
            }
            model_list = ", ".join(blocking_models)

            error_message = f"Cannot delete: This item is used in {model_list}. Try deactivating it instead."

            return Response(
                self.format_payload(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Database Restriction",
                    details=error_message
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        return None

    def _format_to_envelope(self, response: Response) -> Response:
        """Wraps standard DRF responses in the 'error' JSON envelope."""
        http_code_to_message = {v.value: v.phrase for v in HTTPStatus}

        status_msg = http_code_to_message.get(
            response.status_code,
            "Oops something went wrong, Please try again later...!",
        )

        response.data = self.format_payload(
            status_code=response.status_code,
            message=status_msg,
            details=response.data
        )
        return response

    @staticmethod
    def format_payload(status_code: int, message: str, details: Any) -> dict:
        """Helper to maintain the Enterprise Response Envelope structure."""
        return {
            "success": False,
            "error": {
                "status_code": status_code,
                "message": message,
                "details": details,
            },
        }


def general_exception_handler(exc: Exception, context: dict[str, Any]) -> Response:
    """The function DRF calls."""
    return APIExceptionHandler(exc, context).handle()


class EmailExceptionHandler:
    """Handles email-specific logic separately to keep concerns clean."""

    @classmethod
    def handle(cls, e: Exception) -> tuple[bool, str]:
        logger.error(f"Email system error: {str(e)}")

        if isinstance(e, (socket.gaierror, socket.timeout, TimeoutError, SMTPConnectError)):
            return False, "Network error or timeout. Please check your internet connection and try again."

        if isinstance(e, SMTPAuthenticationError):
            return False, "Email service is temporarily unavailable. Please contact support if this persists."

        if isinstance(e, SMTPException):
            return False, "We couldn't deliver the email. Please double-check the address or try again."

        return False, "Oops, something went wrong while sending the email. Please try again."


def handle_mail_exception(e: Exception) -> tuple[bool, str]:
    """Legacy wrapper for Email Exception."""
    return EmailExceptionHandler.handle(e)
