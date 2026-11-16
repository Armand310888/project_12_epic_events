"""
Provide customer management services
with authentication and authorization.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from epic_events.models import Customer
from epic_events.security.authorizations import (
    Permission,
    require_general_permission,
)
from epic_events.services.auth_service import get_current_employee
from epic_events.services.validators import validate_id


def get_all_customers(session: Session) -> list[Customer]:
    """
    Retrieve all customers accessible to the authenticated employee.

    Require authentication and the CUSTOMER_READ permission before
    querying the database.

    Return an empty list if no customers exist.
    Raise PermissionDeniedError if access is unauthorized.
    """
    employee = get_current_employee(session)

    require_general_permission(employee, Permission.CUSTOMER_READ)

    statement = select(Customer)
    return list(session.scalars(statement).all())


def get_customer_by_id(
    session: Session,
    customer_id: int,
) -> Customer | None:
    """
    Retrieve a customer by ID for an authenticated and authorized employee.

    Require the CUSTOMER_READ permission before querying the database.

    Return the customer if found, or None if no customer matches the ID.
    Raise PermissionDeniedError if access is unauthorized.
    """
    employee = get_current_employee(session)

    require_general_permission(employee, Permission.CUSTOMER_READ)

    customer_id = validate_id(customer_id)

    return session.get(Customer, customer_id)
