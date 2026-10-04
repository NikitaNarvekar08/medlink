import re

from django.core.exceptions import ValidationError


def validate_phone(value):
    """Exactly 10 digits, numbers only."""
    if not re.fullmatch(r"[0-9]{10}", value or ""):
        raise ValidationError(
            "Enter a valid 10-digit phone number (digits only, no spaces or +91)."
        )


def validate_email_strict(value):
    """Must contain '@' and a domain such as example.com."""
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}", value or ""):
        raise ValidationError(
            "Enter a valid email address that contains '@', e.g. name@example.com."
        )


def validate_city(value):
    """Letters, spaces, dots and hyphens only."""
    if not re.fullmatch(r"[A-Za-z][A-Za-z .\-]{1,99}", (value or "").strip()):
        raise ValidationError("Enter a valid city name (letters only).")