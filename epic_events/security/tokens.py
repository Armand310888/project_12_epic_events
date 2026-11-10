"""Provide secure JWT generation and verification for employee authentication."""

import os
import uuid
from datetime import UTC, datetime, timedelta

import jwt

SECRET_KEY = os.environ["EPIC_EVENTS_JWT_SECRET_KEY"]


def create_access_token(id_employee: int) -> str:
    """Create a signed JWT for an authenticated employee."""
    now = datetime.now(UTC)

    payload = {
        "sub": str(id_employee),
        "iat": now,
        "exp": now + timedelta(hours=8),
        "jti": str(uuid.uuid4())
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm="HS256",
    )

    return token


def verify_access_token():
    """Validate a JWT and extract the authenticated employee's identifier."""
