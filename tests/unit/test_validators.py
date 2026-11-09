
"""Unit tests for input validation and normalization functions."""

import pytest

from epic_events.services.validators import (
    validate_full_name,
    validate_id,
    validate_password,
    validate_user_email,
)

# full_name validation


def test_validate_full_name_accepts_valid_name():
    """Verify that a valid name is accepted and normalized."""
    result = validate_full_name("  Jean Dupont  ")

    assert result == "Jean Dupont"


def test_validate_full_name_rejects_empty_name():
    """Verify that an empty name is rejected."""
    with pytest.raises(ValueError):
        validate_full_name("   ")


def test_validate_full_name_rejects_invalid_type():
    """Verify that a non-string name is rejected."""
    with pytest.raises(TypeError):
        validate_full_name(123)


# Email validation


def test_validate_user_email_accepts_valid_email():
    """Verify that a valid email address is accepted."""
    result = validate_user_email("  jean@example.com  ")

    assert result == "jean@example.com"


def test_validate_user_email_rejects_invalid_email():
    """Verify that an invalid email address is rejected."""
    with pytest.raises(ValueError):
        validate_user_email("invalid-email")


def test_validate_user_email_rejects_invalid_type():
    """Verify that a non-string email is rejected."""
    with pytest.raises(TypeError):
        validate_user_email(123)


# Password validation


def test_validate_password_accepts_valid_password():
    """Verify that a password meeting the policy is accepted."""
    password = "SecurePassword123!"

    result = validate_password(password)

    assert result == password


def test_validate_password_rejects_short_password():
    """Verify that a password shorter than 10 characters is rejected."""
    with pytest.raises(ValueError):
        validate_password("Short1!")


def test_validate_password_rejects_missing_digit():
    """Verify that a password without a digit is rejected."""
    with pytest.raises(ValueError):
        validate_password("SecurePassword!")


def test_validate_password_rejects_missing_special_character():
    """Verify that a password without a special character is rejected."""
    with pytest.raises(ValueError):
        validate_password("SecurePassword123")


def test_validate_password_rejects_missing_uppercase():
    """Verify that a password without an uppercase letter is rejected."""
    with pytest.raises(ValueError):
        validate_password("securepassword123!")


# ID validation


def test_validate_id_accepts_positive_integer():
    """Verify that a positive integer identifier is accepted."""
    result = validate_id(12)

    assert result == 12


def test_validate_id_rejects_zero():
    """Verify that zero is rejected as an identifier."""
    with pytest.raises(ValueError):
        validate_id(0)


def test_validate_id_rejects_negative_integer():
    """Verify that a negative identifier is rejected."""
    with pytest.raises(ValueError):
        validate_id(-5)


def test_validate_id_rejects_string():
    """Verify that a string identifier is rejected."""
    with pytest.raises(TypeError):
        validate_id("12")


def test_validate_id_rejects_boolean():
    """Verify that a boolean identifier is rejected."""
    with pytest.raises(TypeError):
        validate_id(True)
