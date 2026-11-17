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
from epic_events.services.validators import (
    validate_company_name,
    validate_full_name,
    validate_id,
    validate_phone_number,
    validate_user_email,
)


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


def create_customer(
    session: Session,
    full_name: str,
    email: str,
    phone_number: str,
    company: str | None = None,
) -> Customer:
    """
    Create a new customer assigned to the authenticated sales employee.

    Require an authenticated employee with the CUSTOMER_CREATE permission.
    Validate and normalize the customer's name, email, phone number, and
    optional company name. Ensure that the email address is not already
    associated with another customer.

    Automatically assign the customer to the authenticated sales employee.
    Add the new customer to the session without committing the transaction.

    Return the newly created Customer instance.

    Raise PermissionDeniedError if the current employee is unauthorized.
    Raise TypeError or ValueError if the provided data is invalid.
    Raise ValueError if the email address is already registered.
    """
    employee = get_current_employee(session)
    require_general_permission(employee, Permission.CUSTOMER_CREATE)

    full_name = validate_full_name(full_name)
    email = validate_user_email(email)
    phone_number = validate_phone_number(phone_number)

    if company is not None:
        company = validate_company_name(company)

    statement = select(Customer).where(Customer.email == email)
    if session.scalar(statement) is not None:
        raise ValueError("A customer with this email already exists.")

    customer = Customer(
        full_name=full_name,
        email=email,
        phone_number=phone_number,
        company=company,
        id_sales_employee=employee.id_employee,
    )

    session.add(customer)
    return customer


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
