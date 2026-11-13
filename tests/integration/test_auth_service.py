"""Integration tests for employee authentication."""

import pytest

from epic_events.security.token_storage import save_token
from epic_events.security.tokens import (
    create_access_token,
    verify_access_token,
)
from epic_events.services.auth_service import (
    AlreadyAuthenticatedError,
    authenticate_employee,
    get_current_employee,
    login_employee,
)

# Test "authenticate_employee"


def test_authenticate_employee_success(
    db_session,
    sample_employee,
    test_employee_password,
):
    """Verify that valid credentials authenticate an active employee."""
    employee = authenticate_employee(
        db_session,
        sample_employee.email,
        test_employee_password,
    )

    assert employee is sample_employee


@pytest.mark.parametrize(
    "invalid_field",
    ["email", "password"],
    ids=["unknown_email", "wrong_password"],
)
def test_authenticate_employee_invalid_credentials(
    db_session,
    sample_employee,
    test_employee_password,
    invalid_field,
):
    """Verify that invalid credentials prevent authentication."""
    email = sample_employee.email
    password = test_employee_password

    if invalid_field == "email":
        email = "wrongemail@example.com"
    else:
        password = "wrongpassword"

    employee = authenticate_employee(
        db_session,
        email,
        password,
    )

    assert employee is None


def test_authenticate_employee_inactive_account(
    db_session,
    sample_employee,
    test_employee_password,
):
    """Verify that authentication fails for a deactivated employee."""
    sample_employee.is_active = False

    employee = authenticate_employee(
        db_session,
        sample_employee.email,
        test_employee_password,
    )

    assert employee is None


# Test "login_employee"


def test_login_employee_success(
    db_session,
    sample_employee,
    mock_token_file,
    test_employee_password,
):
    """
    Verify that successful login authenticates
    an employee and stores a JWT.
    """
    employee = login_employee(
        db_session,
        sample_employee.email,
        test_employee_password,
    )

    assert employee is sample_employee

    token = mock_token_file.read_text()

    id_employee = verify_access_token(token)

    assert id_employee == sample_employee.id_employee


def test_login_employee_rejects_invalid_password(
    db_session,
    sample_employee,
    mock_token_file,
):
    """Verify that an invalid password returns None without storing a JWT."""
    assert not mock_token_file.exists()

    employee = login_employee(
        db_session,
        sample_employee.email,
        password="wrongpassword",
    )

    assert employee is None
    assert not mock_token_file.exists()


def test_login_employee_rejects_existing_session(
    db_session,
    sample_employee,
    mock_token_file,
    test_employee_password,
):
    """
    Verify that login is denied without
    replacing an active session token.
    """
    token = create_access_token(sample_employee.id_employee)
    save_token(token)

    with pytest.raises(AlreadyAuthenticatedError):
        login_employee(
            db_session,
            sample_employee.email,
            test_employee_password,
        )

    assert mock_token_file.read_text() == token


# Test "get_current_employee"


def test_get_current_employee_success(
    db_session,
    sample_employee,
    mock_token_file,
):
    """Verify that a valid stored JWT retrieves the active employee."""
    token = create_access_token(sample_employee.id_employee)
    save_token(token)

    employee = get_current_employee(db_session)

    assert employee is sample_employee
    assert mock_token_file.read_text() == token


def test_get_current_employee_without_token(
    db_session,
    mock_token_file,
):
    """Verify that a missing stored JWT returns None."""
    assert not mock_token_file.exists()

    employee = get_current_employee(db_session)

    assert employee is None
    assert not mock_token_file.exists()


def test_get_current_employee_rejects_invalid_token(
    db_session,
    mock_token_file,
):
    """Verify that an invalid stored JWT is rejected and deleted."""
    save_token("invalid.jwt.token")

    employee = get_current_employee(db_session)

    assert employee is None
    assert not mock_token_file.exists()


def test_get_current_employee_rejects_inactive_employee(
    db_session,
    sample_employee,
    mock_token_file,
):
    """Verify that an inactive employee cannot resume a stored session."""
    token = create_access_token(sample_employee.id_employee)
    save_token(token)

    sample_employee.is_active = False

    employee = get_current_employee(db_session)

    assert employee is None
    assert not mock_token_file.exists()


def test_get_current_employee_rejects_unknown_employee(
    db_session,
    sample_employee,
    mock_token_file,
):
    """
    Verify that a JWT referencing a missing employee
    is rejected and deleted.
    """
    unknown_id = sample_employee.id_employee + 1_000_000_000
    token = create_access_token(unknown_id)
    save_token(token)

    employee = get_current_employee(db_session)

    assert employee is None
    assert not mock_token_file.exists()
