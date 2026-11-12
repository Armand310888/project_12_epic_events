"""Provide business logic for employee authentication and access management."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from epic_events.models import Employee
from epic_events.security.passwords import hash_password, verify_password
from epic_events.security.token_storage import (
    delete_token,
    load_token,
    save_token,
)
from epic_events.security.tokens import (
    create_access_token,
    verify_access_token,
)
from epic_events.services.validators import validate_user_email

DUMMY_PASSWORD_HASH = hash_password("DummyPassword123!")


def authenticate_employee(
    session: Session,
    email: str,
    password: str
) -> Employee | None:
    """Authenticate an active employee using email and password."""
    try:
        email = validate_user_email(email)
    except (ValueError, TypeError):
        verify_password(DUMMY_PASSWORD_HASH, password)
        return None

    statement = select(Employee).where(Employee.email == email)
    employee = session.scalar(statement)

    if employee is None:
        verify_password(DUMMY_PASSWORD_HASH, password)
        return None

    if not verify_password(employee.password_hash, password):
        return None

    if not employee.is_active:
        return None

    return employee


def login_employee(
    session: Session,
    email: str,
    password: str,
) -> Employee | None:
    """Authenticate an employee and establish a persistent local session."""

    employee = authenticate_employee(
        session,
        email,
        password
    )

    if employee:
        token = create_access_token(employee.id_employee)
        save_token(token)
        return employee

    return None

