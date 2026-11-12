"""Integration tests for employee authentication."""

from epic_events.security.tokens import verify_access_token
from epic_events.services.auth_service import (
    authenticate_employee,
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


def test_authenticate_employee_unknown_email(
    db_session,
    test_employee_password,
):
    """Verify that authentication fails when the email does not exist."""
    employee = authenticate_employee(
        db_session,
        "wrongemail@example.com",
        test_employee_password,
    )

    assert employee is None


def test_authenticate_employee_wrong_password(
    db_session,
    sample_employee
):
    """Verify that authentication fails with an incorrect password."""
    employee = authenticate_employee(
        db_session,
        sample_employee.email,
        "wrongpassword"
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
