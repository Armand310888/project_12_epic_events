"""Provide secure password hashing and verification using Argon2."""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a password securely using Argon2id."""
    return password_hasher.hash(password)


def verify_password(hashed_password: str, password: str) -> bool:
    """Verify a password against its stored Argon2 hash."""
    try:
        password_hasher.verify(hashed_password, password)
    except VerifyMismatchError:
        return False

    return True
