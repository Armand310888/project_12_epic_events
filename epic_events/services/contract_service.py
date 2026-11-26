
"""
Provide contract management services
with authentication and authorization.
"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from epic_events.models import Contract, Customer
from epic_events.security.authorizations import (
    Permission,
    PermissionDeniedError,
    require_contract_update_permission,
    require_general_permission,
)
from epic_events.services.auth_service import get_current_employee
from epic_events.services.customer_service import get_customer_by_id
from epic_events.services.validators import (
    validate_amount,
    validate_company_name,
    validate_full_name,
    validate_id,
)


def create_contract(
    session: Session,
    total_amount: Decimal,
    outstanding_balance: Decimal,
    customer_id: int,
    is_signed: bool = False,
) -> Contract:
    """
    Create a new contract associated with an existing customer.

    Require an authenticated employee with the CONTRACT_CREATE permission.
    Validate the contract amounts, customer ID, and signing status.
    Ensure that the outstanding balance does not exceed the total amount.

    Verify that the associated customer exists before creating the contract.

    Add the new contract to the session without committing the transaction.

    Return the newly created Contract instance.

    Raise PermissionDeniedError if the current employee is unauthorized.
    Raise TypeError or ValueError if the provided data is invalid.
    Raise ValueError if the customer does not exist or the outstanding
    balance exceeds the total amount.
    """
    current_employee = get_current_employee(session)
    require_general_permission(current_employee, Permission.CONTRACT_CREATE)

    total_amount = validate_amount(total_amount)
    outstanding_balance = validate_amount(outstanding_balance)
    customer_id = validate_id(customer_id)
    if not isinstance(is_signed, bool):
        raise TypeError("'is_signed' value must be a boolean (True or False).")

    if outstanding_balance > total_amount:
        raise ValueError("Outstanding balance cannot exceed total amount.")

    customer = get_customer_by_id(session, customer_id)
    if customer is None:
        raise ValueError(f"Customer with ID {customer_id} does not exist.")

    contract = Contract(
        total_amount=total_amount,
        outstanding_balance=outstanding_balance,
        is_signed=is_signed,
        id_customer=customer_id,
    )

    session.add(contract)
    return contract


def update_contract(
    session: Session,
    contract_id: int,
    total_amount: Decimal | None = None,
    outstanding_balance: Decimal | None = None,
    is_signed: bool | None = None,
    id_customer: int | None = None,
) -> Contract:
    """
    Update an existing contract's information.

    Require an authenticated employee authorized to update the target
    contract. Retrieve the contract and ensure that it exists.

    Validate the provided amounts, signing status, and customer ID.
    If only the total amount changes, automatically recalculate the
    outstanding balance while preserving the amount already paid.

    Reject updates resulting in a negative outstanding balance or
    an outstanding balance greater than the total amount.

    Allow only management employees to change the associated customer.
    Ensure that the new customer exists.

    Update only the provided fields without committing the transaction.

    Return the updated Contract instance.

    Raise PermissionDeniedError if the employee is unauthorized.
    Raise ValueError if the contract or new customer does not exist,
    or if the resulting amounts are inconsistent.
    Raise TypeError or ValueError if the provided data is invalid.
    """
    current_employee = get_current_employee(session)

    contract = get_contract_by_id(session, contract_id)
    if contract is None:
        raise ValueError(f"Contract with ID {contract_id} does not exist.")

    require_contract_update_permission(current_employee, contract)

    # Validate amounts
    if total_amount is not None:
        total_amount = validate_amount(total_amount)

    if outstanding_balance is not None:
        outstanding_balance = validate_amount(outstanding_balance)

    # Recalculate the outstanding balance if only the total changes
    if total_amount is not None and outstanding_balance is None:
        amount_paid = contract.total_amount - contract.outstanding_balance
        outstanding_balance = total_amount - amount_paid

    # Check the consistency of the resulting amounts
    new_total = (
        total_amount
        if total_amount is not None
        else contract.total_amount
    )
    new_balance = (
        outstanding_balance
        if outstanding_balance is not None
        else contract.outstanding_balance
    )

    if new_balance < 0:
        raise ValueError(
            "Total amount cannot be lower than the amount already paid."
        )

    if new_balance > new_total:
        raise ValueError(
            "Outstanding balance cannot exceed total amount."
        )

    if is_signed is not None and not isinstance(is_signed, bool):
        raise TypeError(
            "'is_signed' value must be a boolean (True or False)."
        )

    # Validate customer reassignment
    if id_customer is not None:
        if current_employee.role.name != "management":
            raise PermissionDeniedError(
                "Only management staff can change a contract's customer."
            )

        id_customer = validate_id(id_customer)

        customer = get_customer_by_id(session, id_customer)
        if customer is None:
            raise ValueError(
                f"Customer with ID {id_customer} does not exist."
            )

    # Apply updates
    if total_amount is not None:
        contract.total_amount = total_amount

    if outstanding_balance is not None:
        contract.outstanding_balance = outstanding_balance

    if is_signed is not None:
        contract.is_signed = is_signed

    if id_customer is not None:
        contract.id_customer = id_customer

    return contract


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


def get_contracts(
    session: Session,
    customer_id: int | None = None,
    customer_name: str | None = None,
    company_name: str | None = None,
    unsigned: bool = False,
    unpaid: bool = False,
) -> list[Contract]:
    """
    Retrieve contracts matching optional filters.

    Require the CONTRACT_READ permission.
    Allow filtering by customer ID, customer name, company name,
    unsigned status, and outstanding balance.
    Combine multiple filters using AND logic.

    Return matching contracts, or an empty list if none exist.
    Raise PermissionDeniedError if access is unauthorized.
    Raise TypeError or ValueError if a filter is invalid.
    """
    employee = get_current_employee(session)
    require_general_permission(employee, Permission.CONTRACT_READ)

    statement = select(Contract)

    # Filter by customer attributes
    if customer_id is not None:
        customer_id = validate_id(customer_id)
        statement = statement.where(
            Contract.id_customer == customer_id
        )

    if customer_name is not None or company_name is not None:
        statement = statement.join(
            Customer,
            Contract.id_customer == Customer.id_customer,
        )

    if customer_name is not None:
        customer_name = validate_full_name(customer_name)

        statement = statement.where(
            Customer.full_name.ilike(f"%{customer_name}%")
        )

    if company_name is not None:
        company_name = validate_company_name(company_name)

        statement = statement.where(
            Customer.company.ilike(f"%{company_name}%")
        )

    # Filter by contract status
    if unsigned:
        statement = statement.where(
            Contract.is_signed.is_(False)
        )

    if unpaid:
        statement = statement.where(
            Contract.outstanding_balance > 0
        )

    return list(session.scalars(statement).all())
