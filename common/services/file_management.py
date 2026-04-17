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
    return os.path.join(f"Media/uploads/{folder_base}", clean_name)

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
