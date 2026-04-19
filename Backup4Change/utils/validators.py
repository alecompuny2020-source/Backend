import os
import uuid

import magic
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible
from django.utils.text import slugify


@deconstructible
class MimeTypeValidator:
    """A reusable class-based validator for any file type."""

    def __init__(self, accepted_mimetypes):
        self.accepted_mimetypes = accepted_mimetypes

    def __call__(self, file):
        # Read mime type without corrupting the file pointer
        file.seek(0)
        mime_type = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)

        if mime_type not in self.accepted_mimetypes:
            raise ValidationError(
                f"Unsupported file format: {file_mime_type}. Accepted formats are: {', '.join(self.accepted_mimetypes)}"
            )


image_validator = FileExtensionValidator(["jpg", "jpeg", "png"])
IDs_scan_validator = FileExtensionValidator(["jpg", "jpeg", "png", "pdf"])
contact_validator = FileExtensionValidator(["pdf"])
video_validator = FileExtensionValidator(["mp4", "avi", "mov", "wmv", "webm"])
validate_image_mime = MimeTypeValidator(["image/jpg", "image/jpeg", "image/png"])
validate_video_mime = MimeTypeValidator(
    ["video/mp4", "video/avi", "video/mov", "video/wmv"]
)
validate_scan_mime = MimeTypeValidator(
    ["image/jpg", "image/jpeg", "image/png", "application/pdf"]
)
validate_contract_mime = MimeTypeValidator(
    ["application/pdf"]
)
