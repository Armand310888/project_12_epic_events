
"""
Provide contract management services
with authentication and authorization.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from epic_events.models import Contract
from epic_events.security.authorizations import (
    Permission,
    require_general_permission,
)
from epic_events.services.auth_service import get_current_employee
from epic_events.services.validators import validate_id


def get_all_contracts(session: Session) -> list[Contract]:
    """
    Retrieve all contracts for an authenticated and authorized employee.

    Require the CONTRACT_READ permission before querying the database.

    Return all contracts, or an empty list if none exist.
    Raise PermissionDeniedError if access is unauthorized.
    """
    employee = get_current_employee(session)

    require_general_permission(employee, Permission.CONTRACT_READ)

    statement = select(Contract)

    return list(session.scalars(statement).all())


def get_contract_by_id(
    session: Session,
    contract_id: int,
) -> Contract | None:
    """
    Retrieve a contract by ID for an authenticated and authorized employee.

    Require the CONTRACT_READ permission before querying the database.

    Return the contract if found, or None if no contract matches the ID.
    Raise TypeError or ValueError if the contract ID is invalid.
    Raise PermissionDeniedError if access is unauthorized.
    """
    employee = get_current_employee(session)
    require_general_permission(employee, Permission.CONTRACT_READ)

    contract_id = validate_id(contract_id)

    return session.get(Contract, contract_id)


def get_unsigned_contracts(session: Session) -> list[Contract]:
    """
    Retrieve all unsigned contracts for an authenticated employee.

    Require the CONTRACT_READ permission before querying the database.

    Return contracts whose signature status is False,
    or an empty list if none match.
    Raise PermissionDeniedError if access is unauthorized.
    """
    employee = get_current_employee(session)
    require_general_permission(employee, Permission.CONTRACT_READ)

    statement = select(Contract).where(Contract.is_signed.is_(False))
    return list(session.scalars(statement).all())


def get_contracts_by_customer(
    session: Session,
    customer_id: int,
) -> list[Contract]:
    """
    Retrieve all contracts associated with a specific customer.

    Require the CONTRACT_READ permission before querying the database.
    Validate the customer ID before executing the query.

    Return matching contracts, or an empty list if none exist.
    Raise TypeError or ValueError if the customer ID is invalid.
    Raise PermissionDeniedError if access is unauthorized.
    """
    employee = get_current_employee(session)
    require_general_permission(employee, Permission.CONTRACT_READ)

    customer_id = validate_id(customer_id)

    statement = select(Contract).where(Contract.id_customer == customer_id)
    return list(session.scalars(statement).all())


def get_unpaid_contracts(session: Session) -> list[Contract]:
    """
    Retrieve all contracts with an outstanding balance greater than zero.

    Require the CONTRACT_READ permission before querying the database.

    Return contracts with a positive outstanding balance,
    or an empty list if none match.
    Raise PermissionDeniedError if access is unauthorized.
    """
    employee = get_current_employee(session)
    require_general_permission(employee, Permission.CONTRACT_READ)

    statement = select(Contract).where(Contract.outstanding_balance > 0)
    return list(session.scalars(statement).all())

