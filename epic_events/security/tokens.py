"""Provide secure JWT generation and verification for employee authentication."""

import os
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from jwt.exceptions import InvalidTokenError

from epic_events.services.validators import validate_id

SECRET_KEY = os.environ["EPIC_EVENTS_JWT_SECRET_KEY"]


def create_access_token(id_employee: int) -> str:
    """Create a signed JWT for an authenticated employee."""
    id_employee = validate_id(id_employee)

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


def verify_access_token(token: str) -> int:
    """Validate a JWT and extract the authenticated employee's identifier."""
    payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"],
            options={"require": ["sub", "iat", "exp", "jti"]},
        )

    try:
        id_employee = validate_id(int(payload["sub"]))
    except (ValueError, TypeError) as error:
        raise InvalidTokenError("Invalid employee ID in token.") from error

    return id_employee
