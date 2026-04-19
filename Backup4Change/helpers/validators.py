import os
import uuid

import magic
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible
from django.utils.text import slugify
from rest_framework import serializers


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


class BaseEnterpriseSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        validated_data['updated_on'] = now_iso # Note: Ensure your model supports updated_on
        return super().update(instance, validated_data)
