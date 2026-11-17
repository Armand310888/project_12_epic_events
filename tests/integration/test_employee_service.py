"""Integration tests for employee account management."""

import pytest
from sqlalchemy import func, select

from epic_events.models import Customer, Employee, Role
from epic_events.security.authorizations import PermissionDeniedError
from epic_events.security.passwords import hash_password, verify_password
from epic_events.security.token_storage import save_token
from epic_events.security.tokens import create_access_token
from epic_events.services.employee_service import (
    create_employee,
    delete_employee,
    get_employee_by_id,
    update_employee,
)


@pytest.fixture
def authenticated_manager(db_session, sample_employee, mock_token_file):
    """Authenticate an active management employee."""
    sample_employee.role.name = "management"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    return sample_employee


@pytest.fixture
def target_employee(db_session, sample_employee):
    """Create an employee whose account can be updated."""
    employee = Employee(
        full_name="Original Employee",
        email="original.employee@example.com",
        password_hash=hash_password("OriginalPassword1!"),
        id_role=sample_employee.id_role,
        is_active=True,
    )

    db_session.add(employee)
    db_session.flush()

    return employee

# Test "create_employee"


@pytest.mark.usefixtures("mock_token_file")
def test_create_employee(
    db_session,
    sample_employee,
):
    """Verify that an employee can be created and persisted."""
    sample_employee.role.name = "management"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    full_name = " Test Employee 2 "
    email = " testemployee2@example.com "
    password = "SecurePassword1!"
    id_role = sample_employee.id_role

    employee = create_employee(
        db_session,
        full_name,
        email,
        password,
        id_role,
    )

    db_session.commit()

    statement = (
        select(Employee).where(Employee.id_employee == employee.id_employee)
    )
    result = db_session.scalar(statement)

    assert result is not None
    assert result.full_name == full_name.strip()
    assert result.email == email.strip()
    assert result.password_hash != password
    assert verify_password(result.password_hash, password)
    assert result.id_role == id_role
    assert result.is_active is True


@pytest.mark.usefixtures("mock_token_file")
def test_create_employee_rejects_unknown_role(
    db_session,
    sample_employee,
):
    """Verify that an employee cannot be created with an unknown role."""
    sample_employee.role.name = "management"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    statement = select(func.max(Role.id_role))
    max_role_id = db_session.scalar(statement)

    full_name = "Test Employee"
    email = "testemployee@example.com"
    password = "SecurePassword1!"
    id_role = (max_role_id or 0) + 1

    with pytest.raises(ValueError, match="does not exist"):
        create_employee(
            db_session,
            full_name,
            email,
            password,
            id_role,
        )


@pytest.mark.usefixtures("mock_token_file")
def test_create_employee_rejects_duplicate_email(
    db_session,
    sample_employee,
):
    """Verify that an existing employee email cannot be reused."""
    sample_employee.role.name = "management"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    full_name = "Test Employee"
    email = sample_employee.email
    password = "SecurePassword1!"
    id_role = sample_employee.id_role

    with pytest.raises(ValueError, match="already exist"):
        create_employee(
            db_session,
            full_name,
            email,
            password,
            id_role,
        )


@pytest.mark.usefixtures("mock_token_file")
def test_create_employee_rejects_invalid_password(
    db_session,
    sample_employee,
):
    """
    Verify that employee creation rejects a
    password violating the security policy.
    """
    sample_employee.role.name = "management"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(ValueError):
        create_employee(
            db_session,
            "Test Employee",
            "testemployee@example.com",
            "weak",
            sample_employee.id_role,
        )


@pytest.mark.usefixtures("mock_token_file")
def test_create_employee_requires_authentication(
    db_session,
    sample_employee,
):
    """Verify that employee creation requires authentication."""
    full_name = " Test Employee "
    email = " testemployee@example.com "
    password = "SecurePassword1!"
    id_role = sample_employee.id_role

    with pytest.raises(PermissionDeniedError):
        create_employee(
            db_session,
            full_name,
            email,
            password,
            id_role,
        )


# Test "get_employee_by_id"


def test_get_employee_by_id(db_session, sample_employee):
    """Verify that an existing employee can be retrieved by their ID."""
    employee = get_employee_by_id(db_session, sample_employee.id_employee)

    assert employee is sample_employee


def test_get_employee_by_id_unknown_id(
    db_session,
    sample_employee,
):
    """Verify that an unknown employee ID returns None."""
    unknown_id = sample_employee.id_employee + 1_000_000_000

    assert get_employee_by_id(db_session, unknown_id) is None


def test_get_employee_by_id_validates_id(
    db_session,
):
    """Verify that employee lookup rejects invalid identifiers."""
    with pytest.raises(TypeError):
        get_employee_by_id(db_session, "invalid")


# Test "update_employee"


def test_update_employee_success(
    db_session,
    authenticated_manager,
    target_employee,
):
    """Verify that all employee fields can be updated and persisted."""
    new_role = Role(name="support")
    db_session.add(new_role)
    db_session.flush()

    updated = update_employee(
        db_session,
        target_employee.id_employee,
        full_name=" Updated Employee ",
        email=" updated.employee@example.com ",
        password="NewSecurePassword1!",
        id_role=new_role.id_role,
        is_active=False,
    )

    db_session.commit()

    employee = db_session.get(Employee, target_employee.id_employee)

    assert updated is target_employee
    assert employee.full_name == "Updated Employee"
    assert employee.email == "updated.employee@example.com"
    assert employee.password_hash != "NewSecurePassword1!"
    assert verify_password(employee.password_hash, "NewSecurePassword1!")
    assert employee.id_role == new_role.id_role
    assert employee.is_active is False


def test_update_employee_partial_update(
    db_session,
    authenticated_manager,
    target_employee,
):
    """Verify that updating one field preserves all other fields."""
    original_email = target_employee.email
    original_hash = target_employee.password_hash
    original_role_id = target_employee.id_role
    original_status = target_employee.is_active

    updated = update_employee(
        db_session,
        target_employee.id_employee,
        full_name="New Name",
    )

    assert updated.full_name == "New Name"
    assert updated.email == original_email
    assert updated.password_hash == original_hash
    assert updated.id_role == original_role_id
    assert updated.is_active == original_status


def test_update_employee_without_changes(
    db_session,
    authenticated_manager,
    target_employee,
):
    """Verify that omitting all optional fields preserves the employee."""
    original_name = target_employee.full_name
    original_email = target_employee.email

    updated = update_employee(
        db_session,
        target_employee.id_employee,
    )

    assert updated is target_employee
    assert updated.full_name == original_name
    assert updated.email == original_email


def test_update_employee_accepts_unchanged_email(
    db_session,
    authenticated_manager,
    target_employee,
):
    """Verify that an employee can retain their existing email."""
    updated = update_employee(
        db_session,
        target_employee.id_employee,
        email=target_employee.email,
    )

    assert updated.email == target_employee.email


def test_update_employee_rejects_duplicate_email(
    db_session,
    authenticated_manager,
    target_employee,
):
    """Verify that another employee's email cannot be reused."""
    with pytest.raises(ValueError, match="already exists"):
        update_employee(
            db_session,
            target_employee.id_employee,
            email=authenticated_manager.email,
        )


def test_update_employee_unknown_id(
    db_session,
    authenticated_manager,
    target_employee,
):
    """Verify that an unknown employee ID raises ValueError."""
    unknown_id = target_employee.id_employee + 1_000_000_000

    with pytest.raises(ValueError, match="does not exist"):
        update_employee(
            db_session,
            unknown_id,
            full_name="New Name",
        )


def test_update_employee_validates_id(
    db_session,
    authenticated_manager,
):
    """Verify that employee updates reject invalid identifiers."""
    with pytest.raises(TypeError):
        update_employee(
            db_session,
            "invalid",
            full_name="New Name",
        )


def test_update_employee_rejects_unknown_role(
    db_session,
    authenticated_manager,
    target_employee,
):
    """Verify that an employee cannot receive an unknown role."""
    max_role_id = db_session.scalar(select(func.max(Role.id_role)))
    unknown_role_id = (max_role_id or 0) + 1

    with pytest.raises(ValueError, match="does not exist"):
        update_employee(
            db_session,
            target_employee.id_employee,
            id_role=unknown_role_id,
        )


@pytest.mark.parametrize(
    "field, value",
    [
        ("full_name", "   "),
        ("email", "invalid-email"),
        ("password", "weak"),
        ("id_role", "invalid"),
    ],
    ids=[
        "invalid_name",
        "invalid_email",
        "invalid_password",
        "invalid_role_id",
    ],
)
def test_update_employee_rejects_invalid_fields(
    db_session,
    authenticated_manager,
    target_employee,
    field,
    value,
):
    """Verify that employee updates validate provided values."""
    expected_exception = TypeError if field == "id_role" else ValueError

    with pytest.raises(expected_exception):
        update_employee(
            db_session,
            target_employee.id_employee,
            **{field: value},
        )


@pytest.mark.parametrize(
    "is_active",
    [True, False],
    ids=["activate", "deactivate"],
)
def test_update_employee_changes_active_status(
    db_session,
    authenticated_manager,
    target_employee,
    is_active,
):
    """Verify that management can activate or deactivate an employee."""
    target_employee.is_active = not is_active
    db_session.flush()

    updated = update_employee(
        db_session,
        target_employee.id_employee,
        is_active=is_active,
    )

    assert updated.is_active is is_active


@pytest.mark.parametrize(
    "invalid_status",
    [1, 0, "True", "False"],
    ids=["integer_one", "integer_zero", "string_true", "string_false"],
)
def test_update_employee_rejects_invalid_active_status(
    db_session,
    authenticated_manager,
    target_employee,
    invalid_status,
):
    """Verify that account status only accepts boolean values."""
    with pytest.raises(TypeError):
        update_employee(
            db_session,
            target_employee.id_employee,
            is_active=invalid_status,
        )


def test_update_employee_does_not_apply_partial_changes(
    db_session,
    authenticated_manager,
    target_employee,
):
    """Verify that invalid input leaves other attributes unchanged."""
    original_name = target_employee.full_name

    with pytest.raises(ValueError, match="does not exist"):
        update_employee(
            db_session,
            target_employee.id_employee,
            full_name="New Name",
            id_role=1_000_000_000,
        )

    assert target_employee.full_name == original_name


def test_update_employee_requires_authentication(
    db_session,
    sample_employee,
    target_employee,
    mock_token_file,
):
    """Verify that updating an employee requires authentication."""
    sample_employee.role.name = "management"
    db_session.flush()

    assert not mock_token_file.exists()

    with pytest.raises(PermissionDeniedError):
        update_employee(
            db_session,
            target_employee.id_employee,
            full_name="New Name",
        )


@pytest.mark.usefixtures("mock_token_file")
@pytest.mark.parametrize(
    "role_name",
    ["sales", "support"],
)
def test_update_employee_denies_unauthorized_roles(
    db_session,
    sample_employee,
    target_employee,
    role_name,
):
    """Verify that sales and support employees cannot update accounts."""
    sample_employee.role.name = role_name
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(PermissionDeniedError):
        update_employee(
            db_session,
            target_employee.id_employee,
            full_name="New Name",
        )


@pytest.mark.usefixtures("mock_token_file")
def test_update_employee_denies_inactive_manager(
    db_session,
    sample_employee,
    target_employee,
):
    """Verify that an inactive manager cannot update employees."""
    sample_employee.role.name = "management"
    sample_employee.is_active = False
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(PermissionDeniedError):
        update_employee(
            db_session,
            target_employee.id_employee,
            full_name="New Name",
        )


@pytest.mark.usefixtures("mock_token_file")
def test_update_employee_denies_unknown_role(
    db_session,
    sample_employee,
    target_employee,
):
    """Verify that employees with unknown roles cannot update accounts."""
    # sample_employee has the unknown role "Test Role".
    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(PermissionDeniedError):
        update_employee(
            db_session,
            target_employee.id_employee,
            full_name="New Name",
        )


# Test "delete_employee"


def test_delete_employee_success(
    db_session,
    authenticated_manager,
    target_employee,
):
    """Verify that an employee without dependencies can be deleted."""
    employee_id = target_employee.id_employee

    delete_employee(db_session, employee_id)
    db_session.commit()

    assert db_session.get(Employee, employee_id) is None


def test_delete_employee_unknown_id(
    db_session,
    authenticated_manager,
    target_employee,
):
    """Verify that deleting an unknown employee raises ValueError."""
    unknown_id = target_employee.id_employee + 1_000_000_000

    with pytest.raises(ValueError, match="does not exist"):
        delete_employee(db_session, unknown_id)


def test_delete_employee_validates_id(
    db_session,
    authenticated_manager,
):
    """Verify that employee deletion rejects invalid identifiers."""
    with pytest.raises(TypeError):
        delete_employee(db_session, "invalid")


def test_delete_employee_rejects_associated_customer(
    db_session,
    authenticated_manager,
    target_employee,
):
    """Verify that an employee with assigned customers cannot be deleted."""
    customer = Customer(
        full_name="Associated Customer",
        email="associated.customer@example.com",
        phone_number="0102030405",
        id_sales_employee=target_employee.id_employee,
        is_active=True,
    )
    db_session.add(customer)
    db_session.flush()

    with pytest.raises(ValueError, match="associated customers"):
        delete_employee(db_session, target_employee.id_employee)


def test_delete_employee_rejects_assigned_event(
    db_session,
    authenticated_manager,
    target_employee,
    sample_event,
):
    """Verify that an employee assigned to an event cannot be deleted."""
    sample_event.id_support_employee = target_employee.id_employee
    db_session.flush()

    with pytest.raises(ValueError, match="associated events"):
        delete_employee(db_session, target_employee.id_employee)


def test_delete_employee_requires_authentication(
    db_session,
    sample_employee,
    target_employee,
    mock_token_file,
):
    """Verify that deleting an employee requires authentication."""
    sample_employee.role.name = "management"
    db_session.flush()

    assert not mock_token_file.exists()

    with pytest.raises(PermissionDeniedError):
        delete_employee(db_session, target_employee.id_employee)


@pytest.mark.usefixtures("mock_token_file")
@pytest.mark.parametrize(
    "role_name",
    ["sales", "support"],
)
def test_delete_employee_denies_unauthorized_roles(
    db_session,
    sample_employee,
    target_employee,
    role_name,
):
    """Verify that sales and support employees cannot delete accounts."""
    sample_employee.role.name = role_name
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(PermissionDeniedError):
        delete_employee(db_session, target_employee.id_employee)


@pytest.mark.usefixtures("mock_token_file")
def test_delete_employee_denies_inactive_manager(
    db_session,
    sample_employee,
    target_employee,
):
    """Verify that inactive managers cannot delete employee accounts."""
    sample_employee.role.name = "management"
    sample_employee.is_active = False
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(PermissionDeniedError):
        delete_employee(db_session, target_employee.id_employee)


@pytest.mark.usefixtures("mock_token_file")
def test_delete_employee_denies_unknown_role(
    db_session,
    sample_employee,
    target_employee,
):
    """Verify that unknown roles cannot delete employee accounts."""
    # sample_employee has the unknown role "Test Role".
    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(PermissionDeniedError):
        delete_employee(db_session, target_employee.id_employee)
