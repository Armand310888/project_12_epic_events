"""Provide reusable input validation and normalization functions."""

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
