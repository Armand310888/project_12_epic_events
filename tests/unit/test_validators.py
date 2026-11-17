
"""Unit tests for input validation and normalization functions."""

import pytest

from epic_events.services.validators import (
    validate_company_name,
    validate_full_name,
    validate_id,
    validate_password,
    validate_phone_number,
    validate_string_field,
    validate_user_email,
)

# String field validation


def test_validate_string_field_accepts_valid_string():
    """Verify that a valid string is accepted and normalized."""
    result = validate_string_field("  Example  ", "Test field")

    assert result == "Example"


def test_validate_string_field_rejects_empty_string():
    """Verify that an empty string is rejected."""
    with pytest.raises(ValueError):
        validate_string_field("   ", "Test field")


def test_validate_string_field_rejects_invalid_type():
    """Verify that a non-string value is rejected."""
    with pytest.raises(TypeError):
        validate_string_field(123, "Test field")


def test_validate_string_field_rejects_excessive_length():
    """Verify that strings exceeding the maximum length are rejected."""
    with pytest.raises(ValueError):
        validate_string_field("abcdef", "Test field", max_length=5)


def test_validate_string_field_accepts_maximum_length():
    """Verify that a string exactly at the maximum length is accepted."""
    result = validate_string_field("abcde", "Test field", max_length=5)

    assert result == "abcde"


def test_validate_string_field_accepts_unlimited_length():
    """Verify that no maximum length is enforced when omitted."""
    value = "a" * 300

    assert validate_string_field(value, "Test field") == value


# Full name validation


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


def test_validate_full_name_rejects_excessive_length():
    """Verify that full names exceeding their field limit are rejected."""
    with pytest.raises(ValueError):
        validate_full_name("a" * 101)


# Company name validation


def test_validate_company_name_accepts_valid_name():
    """Verify that a company name is accepted and normalized."""
    result = validate_company_name("  Epic Events  ")

    assert result == "Epic Events"


def test_validate_company_name_rejects_excessive_length():
    """Verify that company names exceeding their field limit are rejected."""
    with pytest.raises(ValueError):
        validate_company_name("a" * 251)


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


def test_validate_password_rejects_missing_lowercase():
    """Verify that a password without a lowercase letter is rejected."""
    with pytest.raises(ValueError):
        validate_password("SECUREPASSWORD123!")


def test_validate_password_rejects_invalid_type():
    """Verify that a non-string password is rejected."""
    with pytest.raises(TypeError):
        validate_password(123)


def test_validate_password_accepts_minimum_length():
    """Verify that a password of exactly 10 characters is accepted."""
    password = "Abcdef12!?"

    assert validate_password(password) == password


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


def test_validate_id_rejects_float():
    """Verify that a floating-point identifier is rejected."""
    with pytest.raises(TypeError):
        validate_id(12.0)


# Phone number validation


def test_validate_phone_number_accepts_french_number():
    """Verify that a French phone number is accepted and normalized."""
    result = validate_phone_number(" 06 12 34 56 78 ")

    assert result == "+33612345678"


def test_validate_phone_number_accepts_international_number():
    """Verify that an international phone number is accepted and normalized."""
    result = validate_phone_number("+44 7911 123456")

    assert result == "+447911123456"


def test_validate_phone_number_rejects_unparseable_number():
    """Verify that an unparseable phone number is rejected."""
    with pytest.raises(ValueError):
        validate_phone_number("not-a-phone-number")


def test_validate_phone_number_rejects_invalid_number():
    """Verify that a parseable but invalid phone number is rejected."""
    with pytest.raises(ValueError):
        validate_phone_number("061234")


def test_validate_phone_number_rejects_invalid_type():
    """Verify that a non-string phone number is rejected."""
    with pytest.raises(TypeError):
        validate_phone_number(123456789)
