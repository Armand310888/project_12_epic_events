"""Provide business logic for employee account management."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from epic_events.models import Employee, Role
from epic_events.security.authorizations import (
    Permission,
    require_general_permission,
)
from epic_events.security.passwords import hash_password
from epic_events.services.auth_service import get_current_employee
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
    current_employee = get_current_employee(session)
    require_general_permission(current_employee, Permission.EMPLOYEE_CREATE)

    full_name = validate_full_name(full_name)
    email = validate_user_email(email)
    password = validate_password(password)
    id_role = validate_id(id_role)

    if session.get(Role, id_role) is None:
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


def update_employee(
    session: Session,
    employee_id: int,
    full_name: str | None = None,
    email: str | None = None,
    password: str | None = None,
    id_role: int | None = None,
    is_active: bool | None = None,
) -> Employee:
    """
    Update an employee's account information.

    Require an authenticated employee with the EMPLOYEE_UPDATE permission.
    Retrieve the target employee and update only the provided fields,
    including the account's active status.

    Validate all provided values before applying changes.
    Ensure that the email is not used by another employee and that
    the assigned role exists. Hash the password if it is changed.

    Return the updated employee without committing the transaction.

    Raise PermissionDeniedError if the current employee is unauthorized.
    Raise ValueError if the target employee or assigned role does not exist,
    if the email is already used, or if a provided value is invalid.
    Raise TypeError if a provided value has an invalid type.
    """
    current_employee = get_current_employee(session)
    require_general_permission(current_employee, Permission.EMPLOYEE_UPDATE)

    employee = get_employee_by_id(session, employee_id)

    if employee is None:
        raise ValueError(f"Employee with ID {employee_id} does not exist.")

    if full_name is not None:
        full_name = validate_full_name(full_name)

    if email is not None:
        email = validate_user_email(email)
        statement = select(Employee).where(
            Employee.email == email,
            Employee.id_employee != employee_id,
        )

        if session.scalar(statement) is not None:
            raise ValueError("An employee with this email already exists.")

    if password is not None:
        password = validate_password(password)

    if id_role is not None:
        id_role = validate_id(id_role)
        if session.get(Role, id_role) is None:
            raise ValueError(f"Role with ID {id_role} does not exist.")

    if is_active is not None and not isinstance(is_active, bool):
        raise TypeError("'is_active' value must be a boolean (True or False).")

    if full_name is not None:
        employee.full_name = full_name

    if email is not None:
        employee.email = email

    if password is not None:
        hashed_password = hash_password(password)
        employee.password_hash = hashed_password

    if id_role is not None:
        employee.id_role = id_role

    if is_active is not None:
        employee.is_active = is_active

    return employee


def delete_employee(
    session: Session,
    employee_id: int,
) -> None:
    """
    Delete an employee account.

    Require an authenticated employee with the EMPLOYEE_DELETE permission.
    Retrieve the target employee and ensure that no customers or events
    are associated with the account.

    Mark the employee for deletion without committing the transaction.

    Raise PermissionDeniedError if the current employee is unauthorized.
    Raise ValueError if the target employee does not exist or has
    associated customers or events.
    Raise TypeError or ValueError if the employee ID is invalid.
    """
    current_employee = get_current_employee(session)
    require_general_permission(current_employee, Permission.EMPLOYEE_DELETE)

    employee = get_employee_by_id(session, employee_id)

    if employee is None:
        raise ValueError(f"Employee with ID {employee_id} does not exist.")

    if employee.customers:
        raise ValueError(
            "Cannot delete an employee with associated customers."
        )

    if employee.events:
        raise ValueError(
            "Cannot delete an employee with associated events."
        )

    session.delete(employee)


def get_employee_by_id(
        session: Session,
        id_employee: int,
) -> Employee | None:
    """Retrieve an employee by their ID, or return None if not found."""
    id_employee = validate_id(id_employee)

    return session.get(Employee, id_employee)


def get_role_by_name(session: Session, name: str) -> Role | None:
    """Retrieve a role by its name, or return None if it does not exist."""
    if not isinstance(name, str):
        raise TypeError("Role name must be a string.")

    name = name.strip().lower()

    if not name:
        raise ValueError("Role name cannot be empty.")

    statement = select(Role).where(Role.name == name)

    return session.scalar(statement)