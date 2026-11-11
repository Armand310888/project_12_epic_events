"""Unit tests for JWT generation and verification."""

import jwt
import pytest

from epic_events.security import tokens

TEST_SECRET_KEY = (
    "396d3d54ccd4084662e426ed7313e4f4ba5fd1b69120891ccefbdac81619b640"
)


def test_create_access_token(monkeypatch):
    """Verify that a valid JWT is generated for an employee."""
    id_employee = 12

    monkeypatch.setattr(tokens, "SECRET_KEY", TEST_SECRET_KEY)

    token = tokens.create_access_token(id_employee)

    assert isinstance(token, str)

    payload = jwt.decode(
        token,
        TEST_SECRET_KEY,
        algorithms=["HS256"]
    )

    assert payload["sub"] == str(id_employee)
    assert payload["exp"] - payload["iat"] == 8 * 60 * 60
    assert "jti" in payload


def test_create_access_token_unique_jti(monkeypatch):
    """Verify that each generated JWT has a unique identifier."""
    id_employee = 12

    monkeypatch.setattr(tokens, "SECRET_KEY", TEST_SECRET_KEY)

    token_1 = tokens.create_access_token(id_employee)
    token_2 = tokens.create_access_token(id_employee)

    payload_token_1 = jwt.decode(
        token_1,
        TEST_SECRET_KEY,
        algorithms=["HS256"]
    )

    payload_token_2 = jwt.decode(
        token_2,
        TEST_SECRET_KEY,
        algorithms=["HS256"]
    )

    assert payload_token_1["jti"] != payload_token_2["jti"]


def test_create_access_token_rejects_invalid_id():
    """Verify that token generation rejects an invalid employee ID."""
    id_employee = "wrongid"

    with pytest.raises(TypeError):
        tokens.create_access_token(id_employee)
