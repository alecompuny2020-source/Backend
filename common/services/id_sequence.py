from django.db import transaction


def generate_secure_employee_number(prefix_code: str, padding_length: int = 5) -> str:
    """
    Thread-safe, database-locked sequential ID generator.
    Example output: HR-00123, MFG-00456
    """

    prefix = prefix_code.strip().upper()

    with transaction.atomic():
        # select_for_update() locks the sequence row in the database until this transaction finishes
        sequence_tracker, created = EmployeeIDSequence.objects.select_for_update().get_or_create(
            prefix=prefix,
            defaults={'last_sequence': 0}
        )

        # Increment counter
        new_sequence = sequence_tracker.last_sequence + 1
        sequence_tracker.last_sequence = new_sequence
        sequence_tracker.save()

        # Format with zero padding (e.g., 1 -> '00001')
        padded_sequence = str(new_sequence).zfill(padding_length)

        return f"{prefix}-{padded_sequence}"
