"""Integration tests for employee account management."""

import pytest
from sqlalchemy import func, select

from epic_events.models import Employee, Role
from epic_events.security.authorizations import PermissionDeniedError
from epic_events.security.passwords import verify_password
from epic_events.security.token_storage import save_token
from epic_events.security.tokens import create_access_token
from epic_events.services.employee_service import (
    create_employee,
    get_employee_by_id,
)

# Test "create_employee"


@pytest.mark.usefixtures("mock_token_file")
def test_create_employee(
    db_session,
    sample_employee,
):
    """Verify that an employee can be created and persisted."""
    sample_employee.role.name = "management"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    full_name = " Test Employee 2 "
    email = " testemployee2@example.com "
    password = "SecurePassword1!"
    id_role = sample_employee.id_role

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


@pytest.mark.usefixtures("mock_token_file")
def test_create_employee_rejects_unknown_role(
    db_session,
    sample_employee,
):
    """Verify that an employee cannot be created with an unknown role."""
    sample_employee.role.name = "management"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

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


@pytest.mark.usefixtures("mock_token_file")
def test_create_employee_rejects_duplicate_email(
    db_session,
    sample_employee,
):
    """Verify that an existing employee email cannot be reused."""
    sample_employee.role.name = "management"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

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


@pytest.mark.usefixtures("mock_token_file")
def test_create_employee_rejects_invalid_password(
    db_session,
    sample_employee,
):
    """
    Verify that employee creation rejects a
    password violating the security policy.
    """
    sample_employee.role.name = "management"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(ValueError):
        create_employee(
            db_session,
            "Test Employee",
            "testemployee@example.com",
            "weak",
            sample_employee.id_role,
        )


@pytest.mark.usefixtures("mock_token_file")
def test_create_employee_requires_authentication(
    db_session,
    sample_employee,
):
    """Verify that employee creation requires authentication."""
    full_name = " Test Employee "
    email = " testemployee@example.com "
    password = "SecurePassword1!"
    id_role = sample_employee.id_role

    with pytest.raises(PermissionDeniedError):
        create_employee(
            db_session,
            full_name,
            email,
            password,
            id_role,
        )


# Test "get_employee_by_id"


def test_get_employee_by_id(db_session, sample_employee):
    """Verify that an existing employee can be retrieved by their ID."""
    employee = get_employee_by_id(db_session, sample_employee.id_employee)

    assert employee is sample_employee


def test_get_employee_by_id_unknown_id(
    db_session,
    sample_employee,
):
    """Verify that an unknown employee ID returns None."""
    unknown_id = sample_employee.id_employee + 1_000_000_000

    assert get_employee_by_id(db_session, unknown_id) is None


def test_get_employee_by_id_validates_id(
    db_session,
):
    """Verify that employee lookup rejects invalid identifiers."""
    with pytest.raises(TypeError):
        get_employee_by_id(db_session, "invalid")
