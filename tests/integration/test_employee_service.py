"""Integration tests for employee account management."""

import pytest
from sqlalchemy import select

from epic_events.models import Employee
from epic_events.security.passwords import verify_password
from epic_events.services.employee_service import create_employee


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
