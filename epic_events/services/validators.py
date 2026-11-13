"""Provide reusable input validation and normalization functions."""

from email_validator import EmailNotValidError, validate_email


def validate_full_name(full_name: str) -> str:
    """Validate and normalize a full name."""
    if not isinstance(full_name, str):
        raise TypeError("Full name must be a string.")

    full_name = full_name.strip()

    if not full_name:
        raise ValueError("Full name cannot be empty.")

    if len(full_name) > 100:
        raise ValueError("Full name must not exceed 100 characters.")

    return full_name


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
