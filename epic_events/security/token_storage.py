"""Manage persistent local storage of authentication tokens."""

import os

from platformdirs import user_data_path

DATA_DIR = user_data_path("epic_events")
TOKEN_FILE = DATA_DIR / "token"


def save_token(token: str) -> None:
    """Save an authentication token securely to a local file."""
    try:
        TOKEN_FILE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        TOKEN_FILE.parent.chmod(0o700)

        flags = os.O_WRONLY | os.O_CREAT
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(TOKEN_FILE, flags, mode=0o600)
        os.fchmod(fd, mode=0o600)
        os.ftruncate(fd, 0)

        with os.fdopen(fd, mode="w", encoding="utf-8") as file:
            file.write(token)
    except OSError as error:
        raise TokenStorageError(
            "Unable to save authentication token."
        ) from error


def load_token() -> str | None:
    """Load the locally stored authentication token, if available."""
    try:
        return TOKEN_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError as error:
        raise TokenStorageError(
            "Unable to load authentication token."
        ) from error


def delete_token() -> None:
    """Delete the locally stored authentication token, if it exists."""
    try:
        TOKEN_FILE.unlink(missing_ok=True)
    except OSError as error:
        raise TokenStorageError(
            "Unable to delete authentication token."
        ) from error


class TokenStorageError(Exception):
    """Raised when an authentication token cannot be stored or retrieved."""