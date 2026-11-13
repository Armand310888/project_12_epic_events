"""Integration tests for employee account management."""

import pytest
from sqlalchemy import func, select

from epic_events.models import Employee, Role
from epic_events.security.passwords import verify_password
from epic_events.services.employee_service import (
    create_employee,
    get_employee_by_id,
)

# Test "create_employee"


def test_create_employee(db_session, sample_role):
    """Verify that an employee can be created and persisted."""
    full_name = " Test Employee "
    email = " testemployee@example.com "
    password = "SecurePassword1!"
    id_role = sample_role.id_role

    employee = create_employee(
        db_session,
        full_name,
        email,
        password,
        id_role,
    )

    db_session.commit()

    statement = (
        select(Employee).where(Employee.id_employee == employee.id_employee)
    )
    result = db_session.scalar(statement)

    assert result is not None
    assert result.full_name == full_name.strip()
    assert result.email == email.strip()
    assert result.password_hash != password
    assert verify_password(result.password_hash, password)
    assert result.id_role == id_role
    assert result.is_active is True


def test_create_employee_rejects_unknown_role(db_session):
    """Verify that an employee cannot be created with an unknown role."""
    statement = select(func.max(Role.id_role))
    max_role_id = db_session.scalar(statement)

    full_name = "Test Employee"
    email = "testemployee@example.com"
    password = "SecurePassword1!"
    id_role = (max_role_id or 0) + 1

    with pytest.raises(ValueError, match="does not exist"):
        create_employee(
            db_session,
            full_name,
            email,
            password,
            id_role,
        )


def test_create_employee_rejects_duplicate_email(
    db_session,
    sample_employee,
):
    """Verify that an existing employee email cannot be reused."""
    full_name = "Test Employee"
    email = sample_employee.email
    password = "SecurePassword1!"
    id_role = sample_employee.id_role

    with pytest.raises(ValueError, match="already exist"):
        create_employee(
            db_session,
            full_name,
            email,
            password,
            id_role,
        )


@pytest.mark.parametrize(
    "password, expected_error",
    [
        ("Wrongpassword!", "at least one digit"),
        ("short1!", "at least 10"),
        ("lowercase123!", "at least one uppercase"),
        ("UPPERCASE123!", "at least one lowercase"),
    ],
)
def test_create_employee_rejects_invalid_password(
    db_session,
    sample_role,
    password,
    expected_error,
):
    """
    Verify that employee creation rejects a
    password violating the security policy.
    """
    with pytest.raises(ValueError, match=expected_error):
        create_employee(
            db_session,
            "Test Employee",
            "testemployee@example.com",
            password,
            sample_role.id_role,
        )


# Test "get_employee_by_id"


def test_get_employee_by_id(db_session, sample_employee):
    """Verify that an existing employee can be retrieved by their ID."""
    employee = get_employee_by_id(db_session, sample_employee.id_employee)

    assert employee is sample_employee
