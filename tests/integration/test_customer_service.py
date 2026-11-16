"""Integration tests for customer management services."""

import pytest

from epic_events.models import Customer, Role
from epic_events.security.authorizations import PermissionDeniedError
from epic_events.security.token_storage import save_token
from epic_events.security.tokens import create_access_token
from epic_events.services.customer_service import (
    get_all_customers,
    get_customer_by_id,
)

# Test "get_all_customers"


@pytest.mark.usefixtures("mock_token_file")
def test_get_all_customers_success(
    db_session,
    sample_employee,
    sample_customer,
):
    """Verify that an authenticated employee can retrieve all customers."""
    sample_employee.role.name = "sales"
    db_session.flush()

    customer_2 = Customer(
        full_name="Second Customer",
        email="customer2@example.com",
        phone_number="0101010101",
        id_sales_employee=sample_employee.id_employee,
        is_active=True,
    )

    customer_3 = Customer(
        full_name="Inactive Customer",
        email="customer3@example.com",
        phone_number="0101010101",
        id_sales_employee=sample_employee.id_employee,
        is_active=False,
    )

    db_session.add_all([customer_2, customer_3])
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    customers = get_all_customers(db_session)

    assert isinstance(customers, list)
    assert {customer.id_customer for customer in customers} == {
        sample_customer.id_customer,
        customer_2.id_customer,
        customer_3.id_customer,
    }


@pytest.mark.usefixtures("mock_token_file")
def test_get_all_customers_empty_database(
    db_session,
    sample_employee,
):
    """Verify that an empty customer table returns an empty list."""
    sample_employee.role.name = "sales"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    customers = get_all_customers(db_session)

    assert customers == []


def test_get_all_customers_requires_authentication(
    db_session,
    mock_token_file,
):
    """Verify that unauthenticated users cannot retrieve customers."""
    assert not mock_token_file.exists()

    with pytest.raises(PermissionDeniedError):
        get_all_customers(db_session)


@pytest.mark.usefixtures("mock_token_file")
def test_get_all_customers_denies_inactive_employee(
    db_session,
    sample_employee,
):
    """Verify that inactive employees cannot retrieve customers."""
    save_token(create_access_token(sample_employee.id_employee))

    sample_employee.is_active = False

    with pytest.raises(PermissionDeniedError):
        get_all_customers(db_session)


@pytest.mark.usefixtures("mock_token_file")
def test_get_all_customers_denies_unknown_role(
    db_session,
    sample_employee,
):
    """Verify that employees with unknown roles cannot retrieve customers."""
    unknown_role = Role(name="unknown")
    db_session.add(unknown_role)
    db_session.flush()

    sample_employee.id_role = unknown_role.id_role
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(PermissionDeniedError):
        get_all_customers(db_session)


# Test "get_customer_by_id"


@pytest.mark.usefixtures("mock_token_file")
def test_get_customer_by_id_success(
    db_session,
    sample_employee,
    sample_customer,
):
    """Verify that an authenticated employee can retrieve a customer by ID."""
    sample_employee.role.name = "sales"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    customer = get_customer_by_id(
        db_session,
        sample_customer.id_customer,
    )

    assert customer is sample_customer


@pytest.mark.usefixtures("mock_token_file")
def test_get_customer_by_id_unknown_id(
    db_session,
    sample_employee,
    sample_customer,
):
    """Verify that an unknown customer ID returns None."""
    sample_employee.role.name = "sales"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    unknown_id = sample_customer.id_customer + 1_000_000_000

    customer = get_customer_by_id(db_session, unknown_id)

    assert customer is None


@pytest.mark.usefixtures("mock_token_file")
@pytest.mark.parametrize(
    "customer_id",
    [
        "1",
        1.5,
        None,
        True,
        [],
    ],
    ids=["string", "float", "none", "boolean", "list"],
)
def test_get_customer_by_id_rejects_invalid_type(
    db_session,
    sample_employee,
    customer_id,
):
    """Verify that customer IDs must be integers."""
    sample_employee.role.name = "sales"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(TypeError, match="ID must be a positive integer"):
        get_customer_by_id(db_session, customer_id)


@pytest.mark.usefixtures("mock_token_file")
@pytest.mark.parametrize(
    "customer_id",
    [0, -1],
    ids=["zero", "negative"],
)
def test_get_customer_by_id_rejects_nonpositive_id(
    db_session,
    sample_employee,
    customer_id,
):
    """Verify that customer IDs must be strictly positive."""
    sample_employee.role.name = "sales"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(ValueError, match="ID must be a positive integer"):
        get_customer_by_id(db_session, customer_id)


def test_get_customer_by_id_requires_authentication(
    db_session,
    sample_customer,
    mock_token_file,
):
    """Verify that unauthenticated users cannot retrieve a customer."""
    assert not mock_token_file.exists()

    with pytest.raises(PermissionDeniedError):
        get_customer_by_id(db_session, sample_customer.id_customer)


@pytest.mark.usefixtures("mock_token_file")
def test_get_customer_by_id_denies_inactive_employee(
    db_session,
    sample_employee,
    sample_customer,
):
    """Verify that inactive employees cannot retrieve customers."""
    sample_employee.role.name = "sales"
    sample_employee.is_active = False
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(PermissionDeniedError):
        get_customer_by_id(db_session, sample_customer.id_customer)


@pytest.mark.usefixtures("mock_token_file")
def test_get_customer_by_id_denies_unknown_role(
    db_session,
    sample_employee,
    sample_customer,
):
    """Verify that employees with unknown roles cannot retrieve customers."""
    save_token(create_access_token(sample_employee.id_employee))

    # sample_employee has the unknown role "Test Role".
    with pytest.raises(PermissionDeniedError):
        get_customer_by_id(db_session, sample_customer.id_customer)


@pytest.mark.usefixtures("mock_token_file")
def test_get_customer_by_id_returns_inactive_customer(
    db_session,
    sample_employee,
    sample_customer,
):
    """Verify that inactive customers remain accessible for reading."""
    sample_employee.role.name = "sales"
    sample_customer.is_active = False
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    customer = get_customer_by_id(
        db_session,
        sample_customer.id_customer,
    )

    assert customer is sample_customer
    assert customer.is_active is False
