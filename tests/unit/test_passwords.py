"""Unit tests for password hashing and verification using Argon2id."""

import pytest
from argon2.exceptions import InvalidHashError

from epic_events.security.passwords import (
    hash_password,
    verify_password,
)

TEST_PASSWORD = "CorrectPassword"
HASHED_TEST_PASSWORD = hash_password(TEST_PASSWORD)
WRONG_PASSWORD = "WrongPassword"
INVALID_HASH = "invalidhash"


def test_password_hash():
    """Verify that password hashing produces a valid Argon2id hash."""

    assert isinstance(HASHED_TEST_PASSWORD, str)
    assert HASHED_TEST_PASSWORD != TEST_PASSWORD
    assert verify_password(HASHED_TEST_PASSWORD, TEST_PASSWORD) is True
    assert HASHED_TEST_PASSWORD.startswith("$argon2id$")


def test_verify_password_rejects_incorrect_password():
    """Verify that an incorrect password is rejected."""

    assert (
        verify_password(HASHED_TEST_PASSWORD, WRONG_PASSWORD)
        is False
    )


def test_verify_password_raises_exception_for_incorrect_hash():
    """Verify that an incorrect hash raises an exception and is rejected."""

    with pytest.raises(InvalidHashError):
        verify_password(INVALID_HASH, TEST_PASSWORD)
