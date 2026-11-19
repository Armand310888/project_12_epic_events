"""Provide reusable input validation and normalization functions."""

from datetime import datetime
from decimal import Decimal

import phonenumbers
from email_validator import EmailNotValidError, validate_email
from phonenumbers import NumberParseException


def validate_full_name(full_name: str) -> str:
    """Validate and normalize a full name."""
    return validate_string_field(full_name, "Full name", max_length=100)


def validate_user_email(email: str) -> str:
    """Validate and normalize an email."""
    if not isinstance(email, str):
        raise TypeError("Email must be a string.")

    email = email.strip()

    try:
        validated_email = validate_email(
            email,
            check_deliverability=False,
        )
    except EmailNotValidError as error:
        raise ValueError("Invalid email address.") from error

    normalized_email = validated_email.normalized

    if len(normalized_email) > 250:
        raise ValueError("Email must not exceed 250 characters.")

    return normalized_email


def validate_password(password: str) -> str:
    """Validate a password against the application's security policy."""
    if not isinstance(password, str):
        raise TypeError("Password must be a string.")

    if len(password) < 10 or len(password) > 128:
        raise ValueError(
            "Password must be at least 10 and maximum 128 characters."
        )

    if not any(char.isdigit() for char in password):
        raise ValueError(
            "Password must contain at least one digit."
        )

    if not any(char.isupper() for char in password):
        raise ValueError(
            "Password must contain at least one uppercase letter."
        )

    if not any(char.islower() for char in password):
        raise ValueError(
            "Password must contain at least one lowercase letter."
        )

    if not any(
        not char.isalnum() and not char.isspace()
        for char in password
    ):
        raise ValueError(
            "Password must contain at least one special character."
        )

    return password


def validate_id(identifier: int) -> int:
    """Validate a positive integer identifier."""
    if isinstance(identifier, bool):
        raise TypeError("ID must be a positive integer.")

    if not isinstance(identifier, int):
        raise TypeError("ID must be a positive integer.")

    if identifier <= 0:
        raise ValueError("ID must be a positive integer.")

    return identifier


def validate_phone_number(
    phone_number: str,
    country_code: str = "FR",
) -> str:
    """Validate and normalize a phone number."""
    if not isinstance(phone_number, str):
        raise TypeError("Phone number must be a string.")

    phone_number = phone_number.strip()

    try:
        parsed_phone_number = phonenumbers.parse(phone_number, country_code)
    except NumberParseException as error:
        raise ValueError("Invalid phone number.") from error

    if not phonenumbers.is_valid_number(parsed_phone_number):
        raise ValueError("Invalid phone number.")

    return phonenumbers.format_number(
        parsed_phone_number,
        phonenumbers.PhoneNumberFormat.E164,
    )


def validate_company_name(company_name: str) -> str:
    """Validate and normalize a company name"""
    return validate_string_field(company_name, "Company name", max_length=250)


def validate_string_field(
    value: str,
    field_name: str,
    max_length: int | None = None,
) -> str:
    """Validate and normalize a non-empty string field."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string.")

    value = value.strip()

    if not value:
        raise ValueError(f"{field_name} cannot be empty.")

    if max_length is not None and len(value) > max_length:
        raise ValueError(
            f"{field_name} cannot exceed {max_length} characters."
        )

    return value


def validate_amount(amount: Decimal, field_name: str = "Amount") -> Decimal:
    """
    Validate a non-negative monetary amount
    with at most two decimal places.
    """
    if not isinstance(amount, Decimal):
        raise TypeError(f"{field_name} must be a Decimal.")

    if not amount.is_finite():
        raise ValueError(f"{field_name} must be a finite number.")

    if amount < 0:
        raise ValueError(f"{field_name} cannot be negative.")

    if amount.as_tuple().exponent < -2:
        raise ValueError(f"{field_name} cannot exceed two decimal places.")

    return amount


def validate_address(address: str) -> str:
    """Validate an event location address."""
    return validate_string_field(
        address,
        field_name="Address",
        max_length=250,
    )


def validate_event_name(name: str) -> str:
    "Validate an event name."
    return validate_string_field(
        name,
        field_name="Event name",
        max_length=250
    )


def validate_notes_text(notes: str) -> str:
    "Validate a text of notes."
    return validate_string_field(
        notes,
        field_name="Notes",
        max_length=None,
    )


def validate_attendees_count(attendees_count: int) -> int:
    """Validate an attendees count is a positive integer above zero."""
    if (
        isinstance(attendees_count, bool)
        or not isinstance(attendees_count, int)
    ):
        raise TypeError("Attendees count must be an integer.")

    if attendees_count <= 0:
        raise ValueError("Attendees count must be a positive integer.")

    return attendees_count


def validate_datetime(value: datetime,) -> datetime:
    """
    Validate that the provided value is a datetime instance.

    Return the validated datetime without modification.

    Raise TypeError if the value is not a datetime instance.
    """
    if not isinstance(value, datetime):
        raise TypeError("Value must be a datetime.")

    return value


def validate_start_before_end_datetime(
    start_datetime: datetime,
    end_datetime: datetime,
) -> tuple[datetime, datetime]:
    """
    Validate the chronological order of an event's start and end datetimes.

    Validate both inputs and ensure that the end datetime is strictly
    later than the start datetime.

    Return the validated start and end datetimes as a tuple.

    Raise TypeError if either value is not a datetime instance.
    Raise ValueError if the end datetime is earlier than or equal
    to the start datetime.
    """
    start_datetime = validate_datetime(start_datetime)
    end_datetime = validate_datetime(end_datetime)

    if end_datetime <= start_datetime:
        raise ValueError("End datetime must be later than start datetime.")

    return start_datetime, end_datetime
