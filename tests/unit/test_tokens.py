"""Unit tests for JWT generation and verification."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from epic_events.security import tokens

TEST_SECRET_KEY = (
    "396d3d54ccd4084662e426ed7313e4f4ba5fd1b69120891ccefbdac81619b640"
)
ANOTHER_TEST_KEY = (
    "6987107fb2b2c58cea700cc85fd1f5eecc9a8cfbc7bfa0418075c32d580dd324"
)


@pytest.fixture
def mock_jwt_secret(monkeypatch):
    """Configure a dedicated JWT signing key for tests."""
    monkeypatch.setattr(tokens, "SECRET_KEY", TEST_SECRET_KEY)

# Testing 'create_access_token' function


def test_create_access_token(mock_jwt_secret):
    """Verify that a valid JWT is generated for an employee."""
    id_employee = 12

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


def test_create_access_token_unique_jti(mock_jwt_secret):
    """Verify that each generated JWT has a unique identifier."""
    id_employee = 12

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


@pytest.mark.parametrize(
    "id_employee",
    [
        "wrongid",
        None,
        12.5,
        []
    ],
)
def test_create_access_token_rejects_invalid_id(id_employee):
    """Verify that token generation rejects an invalid employee ID."""
    with pytest.raises(TypeError):
        tokens.create_access_token(id_employee)


# Testing 'verify_access_token' function


def test_verify_access_token_valid(mock_jwt_secret):
    """Verify that a valid JWT returns the authenticated employee's ID."""
    id_employee = 12
    now = datetime.now(UTC)

    payload = {
        "sub": str(id_employee),
        "iat": now,
        "exp": now + timedelta(hours=8),
        "jti": str(uuid.uuid4())
    }

    token = jwt.encode(
        payload,
        TEST_SECRET_KEY,
        algorithm="HS256",
    )

    token_id_employee = tokens.verify_access_token(token)

    assert token_id_employee == id_employee


def test_verify_access_token_invalid_signature(mock_jwt_secret):
    """Verify that a JWT signed with an incorrect key is rejected."""
    id_employee = 12
    now = datetime.now(UTC)

    payload = {
        "sub": str(id_employee),
        "iat": now,
        "exp": now + timedelta(hours=8),
        "jti": str(uuid.uuid4())
    }

    token = jwt.encode(
        payload,
        ANOTHER_TEST_KEY,
        algorithm="HS256",
    )
    assert TEST_SECRET_KEY != ANOTHER_TEST_KEY

    with pytest.raises(jwt.InvalidSignatureError):
        tokens.verify_access_token(token)


@pytest.mark.parametrize(
    "id_employee",
    [
        "wrong-id",
        "12.5",
        "",
        "-1",
        "0",
    ],
)
def test_verify_access_token_invalid_employee_id(mock_jwt_secret, id_employee):
    """Verify that a JWT containing an invalid employee ID is rejected."""
    now = datetime.now(UTC)

    payload = {
        "sub": str(id_employee),
        "iat": now,
        "exp": now + timedelta(hours=8),
        "jti": str(uuid.uuid4())
    }

    token = jwt.encode(
        payload,
        TEST_SECRET_KEY,
        algorithm="HS256",
    )

    with pytest.raises(jwt.InvalidTokenError):
        tokens.verify_access_token(token)


def test_verify_access_token_expired(mock_jwt_secret):
    """Verify that an expired JWT is rejected."""
    id_employee = 12
    now = datetime.now(UTC)

    payload = {
        "sub": str(id_employee),
        "iat": now - timedelta(hours=16),
        "exp": now - timedelta(hours=8),
        "jti": str(uuid.uuid4())
    }

    token = jwt.encode(
        payload,
        TEST_SECRET_KEY,
        algorithm="HS256",
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        tokens.verify_access_token(token)


@pytest.mark.parametrize(
    "missing_claim",
    ["sub", "iat", "exp", "jti"],
)
def test_verify_access_token_missing_required_claim(
    mock_jwt_secret,
    missing_claim,
):
    """Verify that a JWT missing a required claim is rejected."""
    now = datetime.now(UTC)

    payload = {
        "sub": "12",
        "iat": now,
        "exp": now + timedelta(hours=8),
        "jti": str(uuid.uuid4()),
    }

    del payload[missing_claim]

    token = jwt.encode(
        payload,
        TEST_SECRET_KEY,
        algorithm="HS256",
    )

    with pytest.raises(jwt.MissingRequiredClaimError):
        tokens.verify_access_token(token)
