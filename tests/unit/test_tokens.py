"""Unit tests for JWT generation and verification."""

import jwt

from epic_events.security.tokens import SECRET_KEY, create_access_token


def test_create_access_token():
    """Verify that a valid JWT is generated for an employee."""
    id_employee = 12

    token = create_access_token(id_employee)

    assert isinstance(token, str)

    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=["HS256"]
    )

    assert payload["sub"] == str(id_employee)
