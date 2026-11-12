"""Provide business logic for employee account management."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from epic_events.models import Employee, Role
from epic_events.security.passwords import hash_password
from epic_events.services.validators import (
    validate_full_name,
    validate_id,
    validate_password,
    validate_user_email,
)


def create_employee(
        session: Session,
        full_name: str,
        email: str,
        password: str,
        id_role: int,
) -> Employee:
    """Create an employee with a securely hashed password."""
    full_name = validate_full_name(full_name)
    email = validate_user_email(email)
    password = validate_password(password)
    id_role = validate_id(id_role)

    statement = select(Role).where(Role.id_role == id_role)
    if session.scalar(statement) is None:
        raise ValueError(f"Role with ID {id_role} does not exist.")

    statement = select(Employee).where(Employee.email == email)
    if session.scalar(statement) is not None:
        raise ValueError("An employee with this email already exists.")

    hashed_password = hash_password(password)

    employee = Employee(
        full_name=full_name,
        email=email,
        password_hash=hashed_password,
        id_role=id_role,
    )

    session.add(employee)

    return employee


def get_employee_by_id(
        session: Session,
        id_employee: int,
) -> Employee | None:
    """Retrieve an employee by their ID, or return None if not found."""
    id_employee = validate_id(id_employee)

    return session.get(Employee, id_employee)
