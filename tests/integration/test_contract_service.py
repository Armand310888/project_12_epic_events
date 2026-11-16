
"""Integration tests for contract management services."""

from decimal import Decimal

import pytest

from epic_events.models import Contract, Customer
from epic_events.security.authorizations import PermissionDeniedError
from epic_events.security.token_storage import save_token
from epic_events.security.tokens import create_access_token
from epic_events.services.contract_service import (
    get_all_contracts,
    get_contract_by_id,
    get_contracts_by_customer,
    get_unpaid_contracts,
    get_unsigned_contracts,
)

# Test "get_all_contracts"


@pytest.mark.usefixtures("mock_token_file")
def test_get_all_contracts_success(
    db_session,
    sample_employee,
    sample_customer,
    sample_contract,
):
    """Verify that all contracts are returned regardless of signature."""
    sample_employee.role.name = "sales"

    signed_contract = Contract(
        total_amount=Decimal("2000.00"),
        outstanding_balance=Decimal("500.00"),
        is_signed=True,
        id_customer=sample_customer.id_customer,
    )

    db_session.add(signed_contract)
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    contracts = get_all_contracts(db_session)

    assert isinstance(contracts, list)
    assert {contract.id_contract for contract in contracts} == {
        sample_contract.id_contract,
        signed_contract.id_contract,
    }


@pytest.mark.usefixtures("mock_token_file")
def test_get_all_contracts_empty_database(
    db_session,
    sample_employee,
):
    """Verify that an empty contract table returns an empty list."""
    sample_employee.role.name = "sales"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    assert get_all_contracts(db_session) == []


# Test "get_contract_by_id"


@pytest.mark.usefixtures("mock_token_file")
def test_get_contract_by_id_success(
    db_session,
    sample_employee,
    sample_contract,
):
    """Verify that an existing contract can be retrieved by its ID."""
    sample_employee.role.name = "sales"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    contract = get_contract_by_id(
        db_session,
        sample_contract.id_contract,
    )

    assert contract is sample_contract


@pytest.mark.usefixtures("mock_token_file")
def test_get_contract_by_id_unknown_id(
    db_session,
    sample_employee,
    sample_contract,
):
    """Verify that an unknown contract ID returns None."""
    sample_employee.role.name = "sales"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    unknown_id = sample_contract.id_contract + 1_000_000_000

    assert get_contract_by_id(db_session, unknown_id) is None


@pytest.mark.usefixtures("mock_token_file")
@pytest.mark.parametrize(
    "contract_id",
    ["1", 1.5, None, True, []],
    ids=["string", "float", "none", "boolean", "list"],
)
def test_get_contract_by_id_rejects_invalid_type(
    db_session,
    sample_employee,
    contract_id,
):
    """Verify that contract IDs must be integers."""
    sample_employee.role.name = "sales"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(TypeError, match="ID must be a positive integer"):
        get_contract_by_id(db_session, contract_id)


@pytest.mark.usefixtures("mock_token_file")
@pytest.mark.parametrize(
    "contract_id",
    [0, -1],
    ids=["zero", "negative"],
)
def test_get_contract_by_id_rejects_nonpositive_id(
    db_session,
    sample_employee,
    contract_id,
):
    """Verify that contract IDs must be strictly positive."""
    sample_employee.role.name = "sales"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(ValueError, match="ID must be a positive integer"):
        get_contract_by_id(db_session, contract_id)


# Test "get_unsigned_contracts"


@pytest.mark.usefixtures("mock_token_file")
def test_get_unsigned_contracts_success(
    db_session,
    sample_employee,
    sample_customer,
):
    """Verify that only unsigned contracts are returned."""
    sample_employee.role.name = "sales"

    unsigned_contract = Contract(
        total_amount=Decimal("1000.00"),
        outstanding_balance=Decimal("1000.00"),
        is_signed=False,
        id_customer=sample_customer.id_customer,
    )

    signed_contract = Contract(
        total_amount=Decimal("2000.00"),
        outstanding_balance=Decimal("2000.00"),
        is_signed=True,
        id_customer=sample_customer.id_customer,
    )

    db_session.add_all([unsigned_contract, signed_contract])
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    contracts = get_unsigned_contracts(db_session)

    assert {contract.id_contract for contract in contracts} == {
        unsigned_contract.id_contract,
    }


@pytest.mark.usefixtures("mock_token_file")
def test_get_unsigned_contracts_no_matches(
    db_session,
    sample_employee,
    sample_contract,
):
    """Verify that no unsigned contracts returns an empty list."""
    sample_employee.role.name = "sales"
    sample_contract.is_signed = True

    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    assert get_unsigned_contracts(db_session) == []


# Test "get_contracts_by_customer"


@pytest.mark.usefixtures("mock_token_file")
def test_get_contracts_by_customer_success(
    db_session,
    sample_employee,
    sample_customer,
    sample_contract,
):
    """Verify that only contracts belonging to the customer are returned."""
    sample_employee.role.name = "sales"

    second_contract = Contract(
        total_amount=Decimal("1500.00"),
        outstanding_balance=Decimal("500.00"),
        id_customer=sample_customer.id_customer,
    )

    other_customer = Customer(
        full_name="Other Customer",
        email="othercustomer@example.com",
        phone_number="0101010101",
        id_sales_employee=sample_employee.id_employee,
        is_active=True,
    )

    db_session.add_all([second_contract, other_customer])
    db_session.flush()

    other_contract = Contract(
        total_amount=Decimal("800.00"),
        outstanding_balance=Decimal("800.00"),
        id_customer=other_customer.id_customer,
    )

    db_session.add(other_contract)
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    contracts = get_contracts_by_customer(
        db_session,
        sample_customer.id_customer,
    )

    assert {contract.id_contract for contract in contracts} == {
        sample_contract.id_contract,
        second_contract.id_contract,
    }
    assert other_contract not in contracts


@pytest.mark.usefixtures("mock_token_file")
def test_get_contracts_by_customer_no_matches(
    db_session,
    sample_employee,
    sample_contract,
):
    """Verify that an unknown customer ID returns an empty list."""
    sample_employee.role.name = "sales"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    unknown_id = sample_contract.id_customer + 1_000_000_000

    assert get_contracts_by_customer(db_session, unknown_id) == []


@pytest.mark.usefixtures("mock_token_file")
@pytest.mark.parametrize(
    "customer_id",
    ["1", 1.5, None, True, []],
    ids=["string", "float", "none", "boolean", "list"],
)
def test_get_contracts_by_customer_rejects_invalid_type(
    db_session,
    sample_employee,
    customer_id,
):
    """Verify that customer IDs must be integers."""
    sample_employee.role.name = "sales"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(TypeError, match="ID must be a positive integer"):
        get_contracts_by_customer(db_session, customer_id)


@pytest.mark.usefixtures("mock_token_file")
@pytest.mark.parametrize(
    "customer_id",
    [0, -1],
    ids=["zero", "negative"],
)
def test_get_contracts_by_customer_rejects_nonpositive_id(
    db_session,
    sample_employee,
    customer_id,
):
    """Verify that customer IDs must be strictly positive."""
    sample_employee.role.name = "sales"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(ValueError, match="ID must be a positive integer"):
        get_contracts_by_customer(db_session, customer_id)


# Test "get_unpaid_contracts"


@pytest.mark.usefixtures("mock_token_file")
def test_get_unpaid_contracts_success(
    db_session,
    sample_employee,
    sample_contract,
):
    """
    Verify that only contracts with a positive
    outstanding balance are returned.
    """
    sample_employee.role.name = "sales"
    sample_contract.outstanding_balance = Decimal("0.00")

    almost_paid_contract = Contract(
        total_amount=Decimal("1000.00"),
        outstanding_balance=Decimal("0.01"),
        is_signed=True,
        id_customer=sample_contract.id_customer,
    )

    unpaid_contract = Contract(
        total_amount=Decimal("1000.00"),
        outstanding_balance=Decimal("1000.00"),
        is_signed=False,
        id_customer=sample_contract.id_customer,
    )

    db_session.add_all([almost_paid_contract, unpaid_contract])
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    contracts = get_unpaid_contracts(db_session)

    assert {contract.id_contract for contract in contracts} == {
        almost_paid_contract.id_contract,
        unpaid_contract.id_contract,
    }


# Test "contract_read_permissions"


@pytest.mark.usefixtures("mock_token_file")
@pytest.mark.parametrize(
    "role_name",
    ["management", "sales", "support"],
)
def test_contract_read_allows_all_business_roles(
    db_session,
    sample_employee,
    sample_contract,
    role_name,
):
    """Verify that all recognized roles can read contracts."""
    sample_employee.role.name = role_name
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    contracts = get_all_contracts(db_session)

    assert contracts == [sample_contract]


@pytest.mark.usefixtures("mock_token_file")
@pytest.mark.parametrize(
    "read_operation",
    [
        lambda session: get_all_contracts(session),
        lambda session: get_contract_by_id(session, 1),
        lambda session: get_unsigned_contracts(session),
        lambda session: get_contracts_by_customer(session, 1),
        lambda session: get_unpaid_contracts(session),
    ],
    ids=[
        "all_contracts",
        "contract_by_id",
        "unsigned_contracts",
        "contracts_by_customer",
        "unpaid_contracts",
    ],
)
def test_contract_reads_require_authentication(
    db_session,
    read_operation,
):
    """Verify that contract reading requires authentication."""
    with pytest.raises(PermissionDeniedError):
        read_operation(db_session)


@pytest.mark.usefixtures("mock_token_file")
@pytest.mark.parametrize(
    "read_operation",
    [
        lambda session: get_all_contracts(session),
        lambda session: get_contract_by_id(session, 1),
        lambda session: get_unsigned_contracts(session),
        lambda session: get_contracts_by_customer(session, 1),
        lambda session: get_unpaid_contracts(session),
    ],
    ids=[
        "all_contracts",
        "contract_by_id",
        "unsigned_contracts",
        "contracts_by_customer",
        "unpaid_contracts",
    ],
)
def test_contract_reads_deny_inactive_employee(
    db_session,
    sample_employee,
    read_operation,
):
    """Verify that inactive employees cannot read contracts."""
    sample_employee.role.name = "sales"
    sample_employee.is_active = False
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(PermissionDeniedError):
        read_operation(db_session)


@pytest.mark.usefixtures("mock_token_file")
@pytest.mark.parametrize(
    "read_operation",
    [
        lambda session: get_all_contracts(session),
        lambda session: get_contract_by_id(session, 1),
        lambda session: get_unsigned_contracts(session),
        lambda session: get_contracts_by_customer(session, 1),
        lambda session: get_unpaid_contracts(session),
    ],
    ids=[
        "all_contracts",
        "contract_by_id",
        "unsigned_contracts",
        "contracts_by_customer",
        "unpaid_contracts",
    ],
)
def test_contract_reads_deny_unknown_role(
    db_session,
    sample_employee,
    read_operation,
):
    """Verify that unknown roles cannot read contracts."""
    # sample_employee has the unknown role "Test Role".
    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(PermissionDeniedError):
        read_operation(db_session)
