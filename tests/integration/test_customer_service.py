"""Integration tests for customer management services."""

from datetime import UTC, datetime, timedelta

import pytest

from epic_events.models import Customer, Employee
from epic_events.security.authorizations import PermissionDeniedError
from epic_events.security.token_storage import save_token
from epic_events.security.tokens import create_access_token
from epic_events.services.customer_service import (
    create_customer,
    get_all_customers,
    get_customer_by_id,
    update_customer,
)


@pytest.fixture
def owned_customer(db_session, authenticated_sales, sample_customer):
    """Provide a customer assigned to the authenticated sales employee."""
    sample_customer.id_sales_employee = authenticated_sales.id_employee
    db_session.flush()

    return sample_customer


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
    """
    Verify that a customer is created and assigned
    to the current sales employee.
    """
    customer = create_customer(
        db_session,
        full_name="  Jean Dupont  ",
        email="  jean.dupont@example.com  ",
        phone_number="06 12 34 56 78",
        company="  Example Company  ",
    )

    db_session.flush()

    assert customer.id_customer is not None
    assert customer.creation_datetime is not None
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


# Test "update_customer"


def test_update_customer_all_fields(
    db_session,
    authenticated_sales,
    owned_customer,
):
    """Verify that all customer fields can be updated."""
    original_datetime = datetime.now(UTC) - timedelta(days=1)
    owned_customer.last_update_datetime = original_datetime
    db_session.flush()

    customer = update_customer(
        db_session,
        owned_customer.id_customer,
        full_name="  Jean Dupont  ",
        email="  updated.customer@example.com  ",
        phone_number="06 12 34 56 78",
        company="  New Company  ",
        is_active=False,
    )

    db_session.flush()
    db_session.refresh(customer)

    assert customer is owned_customer
    assert (
        customer.last_update_datetime > original_datetime.replace(tzinfo=None)
    )
    assert customer.full_name == "Jean Dupont"
    assert customer.email == "updated.customer@example.com"
    assert customer.phone_number == "+33612345678"
    assert customer.company == "New Company"
    assert customer.is_active is False
    assert customer.id_sales_employee == authenticated_sales.id_employee


def test_update_customer_partial(
    db_session,
    authenticated_sales,
    owned_customer,
):
    """Verify that omitted fields retain their existing values."""
    original_email = owned_customer.email
    original_phone = owned_customer.phone_number
    original_company = "Original Company"
    original_status = owned_customer.is_active

    owned_customer.company = original_company
    db_session.flush()

    customer = update_customer(
        db_session,
        owned_customer.id_customer,
        full_name="Updated Name",
    )

    assert customer.full_name == "Updated Name"
    assert customer.email == original_email
    assert customer.phone_number == original_phone
    assert customer.company == original_company
    assert customer.is_active == original_status


def test_update_customer_clear_company(
    db_session,
    authenticated_sales,
    owned_customer,
):
    """Verify that passing None clears the nullable company field."""
    owned_customer.company = "Original Company"
    db_session.flush()

    customer = update_customer(
        db_session,
        owned_customer.id_customer,
        company=None,
    )

    db_session.flush()

    assert customer.company is None


def test_update_customer_same_email(
    db_session,
    authenticated_sales,
    owned_customer,
):
    """Verify that a customer can retain its current email address."""
    customer = update_customer(
        db_session,
        owned_customer.id_customer,
        email=owned_customer.email,
    )

    assert customer.email == owned_customer.email


def test_update_customer_duplicate_email(
    db_session,
    authenticated_sales,
    owned_customer,
):
    """Verify that another customer's email cannot be reused."""
    other_customer = create_customer(
        db_session,
        full_name="Another Customer",
        email="another.customer@example.com",
        phone_number="0612345678",
    )
    db_session.flush()

    with pytest.raises(ValueError, match="already exists"):
        update_customer(
            db_session,
            owned_customer.id_customer,
            email=other_customer.email,
        )


def test_update_customer_unknown_id(
    db_session,
    authenticated_sales,
    owned_customer,
):
    """Verify that updating an unknown customer raises ValueError."""
    unknown_id = owned_customer.id_customer + 1_000_000_000

    with pytest.raises(ValueError, match="does not exist"):
        update_customer(
            db_session,
            unknown_id,
            full_name="Updated Name",
        )


@pytest.mark.parametrize(
    "invalid_field, invalid_value, expected_error",
    [
        ("full_name", "   ", ValueError),
        ("email", "invalid-email", ValueError),
        ("phone_number", "invalid-number", ValueError),
        ("company", "   ", ValueError),
        ("full_name", 123, TypeError),
        ("is_active", "False", TypeError),
    ],
)
def test_update_customer_invalid_fields(
    db_session,
    authenticated_sales,
    owned_customer,
    invalid_field,
    invalid_value,
    expected_error,
):
    """Verify that invalid update values are rejected."""
    with pytest.raises(expected_error):
        update_customer(
            db_session,
            owned_customer.id_customer,
            **{invalid_field: invalid_value},
        )


@pytest.mark.parametrize(
    "new_status",
    [True, False],
)
def test_update_customer_active_status(
    db_session,
    authenticated_sales,
    owned_customer,
    new_status,
):
    """Verify that customers can be activated and deactivated."""
    owned_customer.is_active = not new_status
    db_session.flush()

    customer = update_customer(
        db_session,
        owned_customer.id_customer,
        is_active=new_status,
    )

    assert customer.is_active is new_status


def test_update_customer_unauthorized_sales(
    db_session,
    authenticated_sales,
    owned_customer,
):
    """
    Verify that a sales employee cannot update
    another employee's customer.
    """
    other_employee = Employee(
        full_name="Other Sales Employee",
        email="other.sales@example.com",
        password_hash="test-password-hash",
        is_active=True,
        id_role=authenticated_sales.id_role,
    )
    db_session.add(other_employee)
    db_session.flush()

    owned_customer.id_sales_employee = other_employee.id_employee
    db_session.flush()

    with pytest.raises(PermissionDeniedError):
        update_customer(
            db_session,
            owned_customer.id_customer,
            full_name="Unauthorized Update",
        )


@pytest.mark.usefixtures("mock_token_file")
@pytest.mark.parametrize(
    "role_name",
    ["management", "support"],
)
def test_update_customer_unauthorized_roles(
    db_session,
    sample_employee,
    sample_customer,
    role_name,
):
    """Verify that unauthorized roles cannot update customers."""
    sample_employee.role.name = role_name
    sample_customer.id_sales_employee = sample_employee.id_employee
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(PermissionDeniedError):
        update_customer(
            db_session,
            sample_customer.id_customer,
            full_name="Unauthorized Update",
        )


def test_update_customer_requires_authentication(
    db_session,
    sample_employee,
    sample_customer,
    mock_token_file,
):
    """Verify that updating a customer requires authentication."""
    sample_employee.role.name = "sales"
    db_session.flush()

    assert not mock_token_file.exists()

    with pytest.raises(PermissionDeniedError):
        update_customer(
            db_session,
            sample_customer.id_customer,
            full_name="Unauthorized Update",
        )
