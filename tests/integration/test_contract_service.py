
"""Integration tests for contract management services."""

from decimal import Decimal

import pytest

from epic_events.models import Contract, Customer, Employee
from epic_events.security.authorizations import PermissionDeniedError
from epic_events.security.token_storage import save_token
from epic_events.security.tokens import create_access_token
from epic_events.services.contract_service import (
    create_contract,
    get_all_contracts,
    get_contract_by_id,
    get_contracts_by_customer,
    get_unpaid_contracts,
    get_unsigned_contracts,
    update_contract,
)

READ_OPERATIONS = [
    lambda session: get_all_contracts(session),
    lambda session: get_contract_by_id(session, 1),
    lambda session: get_unsigned_contracts(session),
    lambda session: get_contracts_by_customer(session, 1),
    lambda session: get_unpaid_contracts(session),
]

READ_OPERATIONS_IDS = [
    "all_contracts",
    "contract_by_id",
    "unsigned_contracts",
    "contracts_by_customer",
    "unpaid_contracts",
]


@pytest.fixture
def owned_contract(
    db_session,
    authenticated_sales,
    sample_customer,
    sample_contract,
):
    """Provide a contract belonging to the authenticated sales employee."""
    sample_customer.id_sales_employee = authenticated_sales.id_employee
    sample_contract.id_customer = sample_customer.id_customer
    sample_contract.total_amount = Decimal("10000.00")
    sample_contract.outstanding_balance = Decimal("6000.00")
    db_session.flush()

    return sample_contract


# Test "get_all_contracts"


@pytest.mark.usefixtures("mock_token_file")
def test_get_all_contracts_success(
    db_session,
    sample_employee,
    sample_contract,
):
    """Verify that all contracts are returned regardless of signature."""
    sample_employee.role.name = "sales"

    signed_contract = Contract(
        total_amount=Decimal("2000.00"),
        outstanding_balance=Decimal("500.00"),
        is_signed=True,
        id_customer=sample_contract.id_customer,
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
    "read_operation",
    [
        get_contract_by_id,
        get_contracts_by_customer,
    ],
    ids=[
        "contract_by_id",
        "contracts_by_customer",
    ],
)
def test_contract_reads_validate_ids(
    db_session,
    sample_employee,
    read_operation,
):
    """Verify that contract read services reject invalid identifiers."""
    sample_employee.role.name = "sales"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(TypeError):
        read_operation(db_session, "invalid_id")


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


# Test contract read permissions


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
    READ_OPERATIONS,
    ids=READ_OPERATIONS_IDS,
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
    READ_OPERATIONS,
    ids=READ_OPERATIONS_IDS,
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
    READ_OPERATIONS,
    ids=READ_OPERATIONS_IDS,
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


# Test "create_contract"


def test_create_contract_success(
    db_session,
    authenticated_manager,
    sample_customer,
):
    """Verify that a contract is created and associated with a customer."""
    contract = create_contract(
        db_session,
        total_amount=Decimal("10000.00"),
        outstanding_balance=Decimal("6000.00"),
        customer_id=sample_customer.id_customer,
    )

    db_session.flush()

    assert contract.id_contract is not None
    assert contract.creation_datetime is not None
    assert contract.total_amount == Decimal("10000.00")
    assert contract.outstanding_balance == Decimal("6000.00")
    assert contract.is_signed is False
    assert contract.id_customer == sample_customer.id_customer
    assert db_session.get(Contract, contract.id_contract) is contract


def test_create_contract_accepts_zero_balance(
    db_session,
    authenticated_manager,
    sample_customer,
):
    """Verify that a fully paid contract can be created."""
    contract = create_contract(
        db_session,
        total_amount=Decimal("1000.00"),
        outstanding_balance=Decimal("0.00"),
        customer_id=sample_customer.id_customer,
        is_signed=True,
    )

    assert contract.outstanding_balance == Decimal("0.00")
    assert contract.is_signed is True


def test_create_contract_rejects_excessive_balance(
    db_session,
    authenticated_manager,
    sample_customer,
):
    """Verify that outstanding balance cannot exceed total amount."""
    with pytest.raises(ValueError, match="cannot exceed"):
        create_contract(
            db_session,
            total_amount=Decimal("1000.00"),
            outstanding_balance=Decimal("1500.00"),
            customer_id=sample_customer.id_customer,
        )


def test_create_contract_unknown_customer(
    db_session,
    authenticated_manager,
    sample_customer,
):
    """Verify that a contract cannot reference an unknown customer."""
    unknown_id = sample_customer.id_customer + 1_000_000_000

    with pytest.raises(ValueError, match="does not exist"):
        create_contract(
            db_session,
            total_amount=Decimal("1000.00"),
            outstanding_balance=Decimal("500.00"),
            customer_id=unknown_id,
        )


@pytest.mark.parametrize(
    "invalid_field, invalid_value, expected_error",
    [
        ("total_amount", -1, TypeError),
        ("total_amount", Decimal("-1.00"), ValueError),
        ("outstanding_balance", Decimal("12.345"), ValueError),
        ("customer_id", "invalid", TypeError),
        ("is_signed", 1, TypeError),
    ],
)
def test_create_contract_invalid_fields(
    db_session,
    authenticated_manager,
    sample_customer,
    invalid_field,
    invalid_value,
    expected_error,
):
    """Verify that invalid contract data is rejected."""
    contract_data = {
        "total_amount": Decimal("1000.00"),
        "outstanding_balance": Decimal("500.00"),
        "customer_id": sample_customer.id_customer,
        "is_signed": False,
    }

    contract_data[invalid_field] = invalid_value

    with pytest.raises(expected_error):
        create_contract(db_session, **contract_data)


def test_create_contract_requires_authentication(
    db_session,
    sample_customer,
    mock_token_file,
):
    """Verify that contract creation requires authentication."""
    assert not mock_token_file.exists()

    with pytest.raises(PermissionDeniedError):
        create_contract(
            db_session,
            total_amount=Decimal("1000.00"),
            outstanding_balance=Decimal("500.00"),
            customer_id=sample_customer.id_customer,
        )


@pytest.mark.usefixtures("mock_token_file")
@pytest.mark.parametrize("role_name", ["sales", "support"])
def test_create_contract_denies_unauthorized_roles(
    db_session,
    sample_employee,
    sample_customer,
    role_name,
):
    """Verify that sales and support employees cannot create contracts."""
    sample_employee.role.name = role_name
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(PermissionDeniedError):
        create_contract(
            db_session,
            total_amount=Decimal("1000.00"),
            outstanding_balance=Decimal("500.00"),
            customer_id=sample_customer.id_customer,
        )


# Test "update_contract"


def test_update_contract_all_fields(
    db_session,
    authenticated_manager,
    sample_contract,
):
    """Verify that contract fields can be updated."""
    contract = update_contract(
        db_session,
        sample_contract.id_contract,
        total_amount=Decimal("12000.00"),
        outstanding_balance=Decimal("8000.00"),
        is_signed=True,
    )

    db_session.flush()

    assert contract is sample_contract
    assert contract.total_amount == Decimal("12000.00")
    assert contract.outstanding_balance == Decimal("8000.00")
    assert contract.is_signed is True


def test_update_contract_partial(
    db_session,
    owned_contract,
):
    """Verify that omitted fields remain unchanged."""
    original_total = owned_contract.total_amount
    original_balance = owned_contract.outstanding_balance
    original_customer_id = owned_contract.id_customer

    contract = update_contract(
        db_session,
        owned_contract.id_contract,
        is_signed=True,
    )

    assert contract.is_signed is True
    assert contract.total_amount == original_total
    assert contract.outstanding_balance == original_balance
    assert contract.id_customer == original_customer_id


def test_update_contract_recalculates_balance(
    db_session,
    owned_contract,
):
    """Verify that changing only the total preserves the amount paid."""
    assert owned_contract.total_amount == Decimal("10000.00")
    assert owned_contract.outstanding_balance == Decimal("6000.00")

    contract = update_contract(
        db_session,
        owned_contract.id_contract,
        total_amount=Decimal("12000.00"),
    )

    assert contract.total_amount == Decimal("12000.00")
    assert contract.outstanding_balance == Decimal("8000.00")


def test_update_contract_rejects_overpayment(
    db_session,
    owned_contract,
):
    """Verify that a new total cannot be lower than the amount already paid."""
    assert owned_contract.outstanding_balance == Decimal("6000.00")

    with pytest.raises(ValueError, match="lower than the amount already paid"):
        update_contract(
            db_session,
            owned_contract.id_contract,
            total_amount=Decimal("3000.00"),
        )


def test_update_contract_accepts_explicit_amounts(
    db_session,
    owned_contract,
):
    """Verify that both contract amounts can be updated explicitly."""
    contract = update_contract(
        db_session,
        owned_contract.id_contract,
        total_amount=Decimal("15000.00"),
        outstanding_balance=Decimal("5000.00"),
    )

    assert contract.total_amount == Decimal("15000.00")
    assert contract.outstanding_balance == Decimal("5000.00")


def test_update_contract_rejects_excessive_balance(
    db_session,
    owned_contract,
):
    """Verify that the resulting balance cannot exceed the total."""
    assert owned_contract.total_amount == Decimal("10000.00")

    with pytest.raises(ValueError, match="cannot exceed"):
        update_contract(
            db_session,
            owned_contract.id_contract,
            outstanding_balance=Decimal("12000.00"),
        )


def test_update_contract_management_can_change_customer(
    db_session,
    authenticated_manager,
    sample_contract,
    sample_customer,
):
    """Verify that management can reassign a contract to another customer."""
    new_customer = Customer(
        full_name="Another Customer",
        email="another.contract.customer@example.com",
        phone_number="+33612345678",
        id_sales_employee=authenticated_manager.id_employee,
    )
    db_session.add(new_customer)
    db_session.flush()

    contract = update_contract(
        db_session,
        sample_contract.id_contract,
        id_customer=new_customer.id_customer,
    )

    assert contract.id_customer == new_customer.id_customer


def test_update_contract_sales_cannot_change_customer(
    db_session,
    owned_contract,
):
    """Verify that sales employees cannot reassign a contract."""
    with pytest.raises(PermissionDeniedError):
        update_contract(
            db_session,
            owned_contract.id_contract,
            id_customer=owned_contract.id_customer,
        )


def test_update_contract_unknown_new_customer(
    db_session,
    authenticated_manager,
    sample_contract,
    sample_customer,
):
    """Verify that reassignment to an unknown customer is rejected."""
    unknown_id = sample_customer.id_customer + 1_000_000_000

    with pytest.raises(ValueError, match="does not exist"):
        update_contract(
            db_session,
            sample_contract.id_contract,
            id_customer=unknown_id,
        )


def test_update_contract_unknown_id(
    db_session,
    authenticated_manager,
    sample_contract,
):
    """Verify that updating an unknown contract raises ValueError."""
    unknown_id = sample_contract.id_contract + 1_000_000_000

    with pytest.raises(ValueError, match="does not exist"):
        update_contract(
            db_session,
            unknown_id,
            is_signed=True,
        )


@pytest.mark.parametrize(
    "invalid_field, invalid_value, expected_error",
    [
        ("total_amount", Decimal("-1.00"), ValueError),
        ("outstanding_balance", Decimal("10.123"), ValueError),
        ("is_signed", "True", TypeError),
        ("id_customer", "invalid", TypeError),
    ],
)
def test_update_contract_invalid_fields(
    db_session,
    authenticated_manager,
    sample_contract,
    invalid_field,
    invalid_value,
    expected_error,
):
    """Verify that invalid update values are rejected."""
    with pytest.raises(expected_error):
        update_contract(
            db_session,
            sample_contract.id_contract,
            **{invalid_field: invalid_value},
        )


def test_update_contract_unauthorized_sales(
    db_session,
    owned_contract,
    authenticated_sales,
):
    """
    Verify that a sales employee cannot update
    another employee's contract.
    """
    other_employee = Employee(
        full_name="Other Sales Employee",
        email="other.sales.contract@example.com",
        password_hash="test-password-hash",
        is_active=True,
        id_role=authenticated_sales.id_role,
    )
    db_session.add(other_employee)
    db_session.flush()

    owned_contract.customer.id_sales_employee = other_employee.id_employee
    db_session.flush()

    with pytest.raises(PermissionDeniedError):
        update_contract(
            db_session,
            owned_contract.id_contract,
            is_signed=True,
        )


def test_update_contract_requires_authentication(
    db_session,
    sample_contract,
    mock_token_file,
):
    """Verify that contract updates require authentication."""
    assert not mock_token_file.exists()

    with pytest.raises(PermissionDeniedError):
        update_contract(
            db_session,
            sample_contract.id_contract,
            is_signed=True,
        )
