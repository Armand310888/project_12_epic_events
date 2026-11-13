"""Provide business logic for employee authentication and access management."""

from jwt.exceptions import InvalidTokenError
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
from epic_events.services.employee_service import get_employee_by_id
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
    current_employee = get_current_employee(session)
    if current_employee:
        raise AlreadyAuthenticatedError(
            "Login denied: an active session already exists. "
            "Please log out first."
        )

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


def get_current_employee(
    session: Session,
) -> Employee | None:
    """
    Retrieve the authenticated employee from a valid stored JWT.

    Return None if no token exists. Delete the stored token and return None
    if it is invalid, expired, or belongs to a missing or inactive employee.
    """
    token = load_token()

    if token:
        try:
            id_employee = verify_access_token(token)
            employee = get_employee_by_id(session, id_employee)
            if employee and employee.is_active:
                return employee
            delete_token()
            return None
        except InvalidTokenError:
            delete_token()
            return None

    return None


class AlreadyAuthenticatedError(Exception):
    """Raised when a login is attempted while a valid session is active."""
