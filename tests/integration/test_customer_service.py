"""Integration tests for customer management services."""

import pytest

from epic_events.models import Customer
from epic_events.security.authorizations import PermissionDeniedError
from epic_events.security.token_storage import save_token
from epic_events.security.tokens import create_access_token
from epic_events.services.customer_service import (
    create_customer,
    get_all_customers,
    get_customer_by_id,
)


@pytest.fixture
def authenticated_sales(
    db_session,
    sample_employee,
    mock_token_file,
):
    """Provide an authenticated sales employee."""
    sample_employee.role.name = "sales"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    return sample_employee

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
    sample_employee.role.name = "sales"
    sample_employee.is_active = False

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(PermissionDeniedError):
        get_all_customers(db_session)


@pytest.mark.usefixtures("mock_token_file")
def test_get_all_customers_denies_unknown_role(
    db_session,
    sample_employee,
):
    """Verify that employees with unknown roles cannot retrieve customers."""
    # sample_employee has the unknown role "Test Role".
    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(PermissionDeniedError):
        get_all_customers(db_session)


# Test get customer by id


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
def test_get_customer_by_id_validates_id(
    db_session,
    sample_employee,
):
    """Verify that customer lookup rejects invalid identifiers."""
    sample_employee.role.name = "sales"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(TypeError):
        get_customer_by_id(db_session, "invalid")


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


# Test customer read permissions


@pytest.mark.usefixtures("mock_token_file")
@pytest.mark.parametrize(
    "role_name",
    ["management", "sales", "support"],
)
def test_customer_read_allows_all_business_roles(
    db_session,
    sample_employee,
    sample_customer,
    role_name,
):
    """Verify that all recognized roles can read customers."""
    sample_employee.role.name = role_name
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    assert get_all_customers(db_session) == [sample_customer]


# Test "create_customer"


def test_create_customer_success(
    db_session,
    authenticated_sales,
):
    """Verify that a customer is created and assigned to the current sales employee."""
    customer = create_customer(
        db_session,
        full_name="  Jean Dupont  ",
        email="  jean.dupont@example.com  ",
        phone_number="06 12 34 56 78",
        company="  Example Company  ",
    )

    db_session.flush()

    assert customer.id_customer is not None
    assert customer.full_name == "Jean Dupont"
    assert customer.email == "jean.dupont@example.com"
    assert customer.phone_number == "+33612345678"
    assert customer.company == "Example Company"
    assert customer.id_sales_employee == authenticated_sales.id_employee
    assert db_session.get(Customer, customer.id_customer) is customer


def test_create_customer_without_company(
    db_session,
    authenticated_sales,
):
    """Verify that the optional company field can be omitted."""
    customer = create_customer(
        db_session,
        full_name="Jean Dupont",
        email="jean.dupont@example.com",
        phone_number="0612345678",
    )

    db_session.flush()

    assert customer.company is None
    assert customer.id_customer is not None


def test_create_customer_rejects_duplicate_email(
    db_session,
    authenticated_sales,
    sample_customer,
):
    """Verify that an existing customer email cannot be reused."""
    with pytest.raises(ValueError, match="already exists"):
        create_customer(
            db_session,
            full_name="Jean Dupont",
            email=sample_customer.email,
            phone_number="0612345678",
        )


@pytest.mark.parametrize(
    "invalid_field, invalid_value, expected_error",
    [
        ("full_name", "   ", ValueError),
        ("email", "invalid-email", ValueError),
        ("phone_number", "invalid-number", ValueError),
        ("company", "   ", ValueError),
        ("full_name", 123, TypeError),
        ("phone_number", 123, TypeError),
    ],
)
def test_create_customer_rejects_invalid_fields(
    db_session,
    authenticated_sales,
    invalid_field,
    invalid_value,
    expected_error,
):
    """Verify that invalid customer fields are rejected."""
    customer_data = {
        "full_name": "Jean Dupont",
        "email": "jean.dupont@example.com",
        "phone_number": "0612345678",
        "company": "Example Company",
    }

    customer_data[invalid_field] = invalid_value

    with pytest.raises(expected_error):
        create_customer(db_session, **customer_data)


def test_create_customer_requires_authentication(
    db_session,
    sample_employee,
    mock_token_file,
):
    """Verify that customer creation requires authentication."""
    sample_employee.role.name = "sales"
    db_session.flush()

    assert not mock_token_file.exists()

    with pytest.raises(PermissionDeniedError):
        create_customer(
            db_session,
            full_name="Jean Dupont",
            email="jean.dupont@example.com",
            phone_number="0612345678",
        )


@pytest.mark.usefixtures("mock_token_file")
@pytest.mark.parametrize(
    "role_name",
    ["management", "support"],
)
def test_create_customer_denies_unauthorized_roles(
    db_session,
    sample_employee,
    role_name,
):
    """Verify that management and support employees cannot create customers."""
    sample_employee.role.name = role_name
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(PermissionDeniedError):
        create_customer(
            db_session,
            full_name="Jean Dupont",
            email="jean.dupont@example.com",
            phone_number="0612345678",
        )


@pytest.mark.usefixtures("mock_token_file")
def test_create_customer_denies_inactive_sales_employee(
    db_session,
    sample_employee,
):
    """Verify that inactive sales employees cannot create customers."""
    sample_employee.role.name = "sales"
    sample_employee.is_active = False
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(PermissionDeniedError):
        create_customer(
            db_session,
            full_name="Jean Dupont",
            email="jean.dupont@example.com",
            phone_number="0612345678",
        )


@pytest.mark.usefixtures("mock_token_file")
def test_create_customer_denies_unknown_role(
    db_session,
    sample_employee,
):
    """Verify that employees with unknown roles cannot create customers."""
    # sample_employee has the unknown role "Test Role".
    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(PermissionDeniedError):
        create_customer(
            db_session,
            full_name="Jean Dupont",
            email="jean.dupont@example.com",
            phone_number="0612345678",
        )
