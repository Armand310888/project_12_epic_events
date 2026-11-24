"""
Provide customer management services
with authentication and authorization.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from epic_events.models import Customer
from epic_events.security.authorizations import (
    Permission,
    require_customer_update_permission,
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


class _UnsetType:
    """Represent a function argument that was not provided."""


_UNSET = _UnsetType()


def get_customers(
    session: Session,
    customer_id: int | None = None,
    customer_name: str | None = None,
) -> list[Customer]:
    """
    Retrieve customers matching optional filters.

    Require the CUSTOMER_READ permission.
    Allow filtering by customer ID and partial customer name.
    Combine multiple filters using AND logic.

    Return matching customers, or an empty list if none exist.
    Raise PermissionDeniedError if access is unauthorized.
    Raise TypeError or ValueError if a filter is invalid.
    """
    employee = get_current_employee(session)

    require_general_permission(employee, Permission.CUSTOMER_READ)

    statement = select(Customer)

    if customer_id is not None:
        customer_id = validate_id(customer_id)

        statement = statement.where(Customer.id_customer == customer_id)

    if customer_name is not None:
        customer_name = validate_full_name(customer_name)

        statement = statement.where(
            Customer.full_name.ilike(f"%{customer_name}%")
        )

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


def update_customer(
    session: Session,
    customer_id: int,
    full_name: str | None = None,
    email: str | None = None,
    phone_number: str | None = None,
    company: str | None | _UnsetType = _UNSET,
    is_active: bool | None = None,
) -> Customer:
    """
    Update an existing customer's information.

    Require an authenticated employee authorized to update the target
    customer. Retrieve the customer and ensure that it exists.

    Validate and normalize the provided name, email, phone number, and
    company name. Ensure that any updated email address is not already
    associated with another customer.

    Update only the provided fields, including the customer's active
    status. The optional company field supports three operations:
    - Omitted (_UNSET): preserve the existing value.
    - String: validate and replace the existing value.
    - None: clear the company field (set it to NULL).

    Return the updated Customer instance without committing the transaction.

    Raise PermissionDeniedError if the current employee is unauthorized.
    Raise ValueError if the customer does not exist or the email is already
    used by another customer.
    Raise TypeError or ValueError if the provided data is invalid.
    """
    current_employee = get_current_employee(session)
    customer = get_customer_by_id(session, customer_id)

    if customer is None:
        raise ValueError(f"Customer with ID {customer_id} does not exist.")

    require_customer_update_permission(current_employee, customer)

    if full_name is not None:
        full_name = validate_full_name(full_name)

    if email is not None:
        email = validate_user_email(email)
        statement = select(Customer).where(
            Customer.email == email,
            Customer.id_customer != customer_id,
        )
        if session.scalar(statement) is not None:
            raise ValueError("A customer with this email already exists.")

    if phone_number is not None:
        phone_number = validate_phone_number(phone_number)

    if company is not _UNSET and company is not None:
        company = validate_company_name(company)

    if is_active is not None and not isinstance(is_active, bool):
        raise TypeError("'is_active' value must be a boolean (True or False).")

    if full_name is not None:
        customer.full_name = full_name

    if email is not None:
        customer.email = email

    if phone_number is not None:
        customer.phone_number = phone_number

    if company is not _UNSET:
        customer.company = company

    if is_active is not None:
        customer.is_active = is_active

    return customer


def reaffect_sales_employee_to_customer():
    pass


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
