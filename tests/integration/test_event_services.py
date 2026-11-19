
"""Integration tests for event management services."""

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import select

from epic_events.models import (
    Contract,
    Customer,
    Employee,
    Event,
    Role,
)
from epic_events.security.authorizations import PermissionDeniedError
from epic_events.security.token_storage import save_token
from epic_events.security.tokens import create_access_token
from epic_events.services.event_service import (
    assign_support_employee_to_event,
    create_event,
    get_all_events,
    get_event_by_id,
    get_events_by_contract,
    get_events_by_customer,
    get_events_by_support_employee,
    get_events_without_support,
    update_event,
)

READ_OPERATIONS = [
    lambda session: get_all_events(session),
    lambda session: get_event_by_id(session, 1),
    lambda session: get_events_without_support(session),
    lambda session: get_events_by_contract(session, 1),
    lambda session: get_events_by_customer(session, 1),
    lambda session: get_events_by_support_employee(session, 1),
]

READ_OPERATIONS_IDS = [
    "all_events",
    "event_by_id",
    "events_without_support",
    "events_by_contract",
    "events_by_customer",
    "events_by_support_employee",
]


@pytest.fixture
def signed_owned_contract(
    db_session,
    authenticated_sales,
    sample_customer,
    sample_contract,
):
    """
    Provide a signed contract belonging to the
    authenticated sales employee.
    """
    sample_customer.id_sales_employee = authenticated_sales.id_employee
    sample_contract.id_customer = sample_customer.id_customer
    sample_contract.is_signed = True
    db_session.flush()

    return sample_contract


@pytest.fixture
def event_data(signed_owned_contract):
    """Provide valid input data for event creation."""
    return {
        "name": "Annual Conference",
        "start_datetime": datetime(2026, 12, 15, 9, 0),
        "end_datetime": datetime(2026, 12, 15, 18, 0),
        "location": "Paris, France",
        "attendees_count": 150,
        "id_contract": signed_owned_contract.id_contract,
        "notes": "Main conference room",
    }


@pytest.fixture
def assigned_event(
    db_session,
    authenticated_support,
    sample_event,
):
    """Provide an event assigned to the authenticated support employee."""
    sample_event.id_support_employee = authenticated_support.id_employee
    sample_event.start_datetime = datetime(2026, 12, 15, 9, 0)
    sample_event.end_datetime = datetime(2026, 12, 15, 18, 0)
    sample_event.notes = "Original notes"
    db_session.flush()

    return sample_event


@pytest.fixture
def support_employee(
    db_session,
    authenticated_manager,
):
    """Provide an active support employee available for event assignment."""
    support_role = db_session.scalar(
        select(Role).where(Role.name == "support")
    )

    if support_role is None:
        support_role = Role(name="support")
        db_session.add(support_role)
        db_session.flush()

    employee = Employee(
        full_name="Support Employee",
        email="support.assignment@example.com",
        password_hash="test-password-hash",
        is_active=True,
        id_role=support_role.id_role,
    )

    db_session.add(employee)
    db_session.flush()

    return employee

# Test "get_all_events"


@pytest.mark.usefixtures("mock_token_file")
def test_get_all_events_success(
    db_session,
    sample_employee,
    sample_event,
):
    """Verify that all existing events are returned."""
    sample_employee.role.name = "sales"

    second_event = Event(
        name="Second Event",
        start_datetime=datetime(2027, 2, 10, 10, 0),
        end_datetime=datetime(2027, 2, 10, 18, 0),
        location="Lyon",
        attendees_count=100,
        notes="Second test event",
        id_contract=sample_event.id_contract,
        id_support_employee=None,
    )

    db_session.add(second_event)
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    events = get_all_events(db_session)

    assert isinstance(events, list)
    assert {event.id_event for event in events} == {
        sample_event.id_event,
        second_event.id_event,
    }


@pytest.mark.usefixtures("mock_token_file")
def test_get_all_events_empty_database(
    db_session,
    sample_employee,
):
    """Verify that an empty event table returns an empty list."""
    sample_employee.role.name = "sales"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    assert get_all_events(db_session) == []


# Test "get_event_by_id"


@pytest.mark.usefixtures("mock_token_file")
def test_get_event_by_id_success(
    db_session,
    sample_employee,
    sample_event,
):
    """Verify that an existing event can be retrieved by its ID."""
    sample_employee.role.name = "sales"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    event = get_event_by_id(
        db_session,
        sample_event.id_event,
    )

    assert event is sample_event


@pytest.mark.usefixtures("mock_token_file")
def test_get_event_by_id_unknown_id(
    db_session,
    sample_employee,
    sample_event,
):
    """Verify that an unknown event ID returns None."""
    sample_employee.role.name = "sales"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    unknown_id = sample_event.id_event + 1_000_000_000

    assert get_event_by_id(db_session, unknown_id) is None


# Test "get_events_without_support"


@pytest.mark.usefixtures("mock_token_file")
def test_get_events_without_support_success(
    db_session,
    sample_employee,
    sample_event,
):
    """Verify that only events without assigned support are returned."""
    sample_employee.role.name = "support"

    assigned_event = Event(
        name="Assigned Event",
        start_datetime=datetime(2027, 2, 10, 10, 0),
        end_datetime=datetime(2027, 2, 10, 18, 0),
        location="Lyon",
        attendees_count=100,
        notes="Support assigned",
        id_contract=sample_event.id_contract,
        id_support_employee=sample_employee.id_employee,
    )

    db_session.add(assigned_event)
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    events = get_events_without_support(db_session)

    assert {event.id_event for event in events} == {
        sample_event.id_event,
    }
    assert assigned_event not in events


@pytest.mark.usefixtures("mock_token_file")
def test_get_events_without_support_no_matches(
    db_session,
    sample_employee,
    sample_event,
):
    """Verify that no unassigned events returns an empty list."""
    sample_employee.role.name = "support"
    sample_event.id_support_employee = sample_employee.id_employee
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    assert get_events_without_support(db_session) == []


# Test "get_events_by_contract"


@pytest.mark.usefixtures("mock_token_file")
def test_get_events_by_contract_success(
    db_session,
    sample_employee,
    sample_contract,
    sample_event,
):
    """Verify that only events belonging to the contract are returned."""
    sample_employee.role.name = "sales"

    other_contract = Contract(
        total_amount=Decimal("2000.00"),
        outstanding_balance=Decimal("1000.00"),
        is_signed=True,
        id_customer=sample_contract.id_customer,
    )

    db_session.add(other_contract)
    db_session.flush()

    second_event = Event(
        name="Second Event",
        start_datetime=datetime(2027, 2, 10, 10, 0),
        end_datetime=datetime(2027, 2, 10, 18, 0),
        location="Lyon",
        attendees_count=100,
        notes="Second event for the same contract",
        id_contract=sample_contract.id_contract,
        id_support_employee=None,
    )

    other_event = Event(
        name="Other Event",
        start_datetime=datetime(2027, 3, 10, 10, 0),
        end_datetime=datetime(2027, 3, 10, 18, 0),
        location="Dijon",
        attendees_count=75,
        notes="Event for another contract",
        id_contract=other_contract.id_contract,
        id_support_employee=None,
    )

    db_session.add_all([second_event, other_event])
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    events = get_events_by_contract(
        db_session,
        sample_contract.id_contract,
    )

    assert {event.id_event for event in events} == {
        sample_event.id_event,
        second_event.id_event,
    }
    assert other_event not in events


@pytest.mark.usefixtures("mock_token_file")
def test_get_events_by_contract_no_matches(
    db_session,
    sample_employee,
    sample_contract,
):
    """Verify that a contract without events returns an empty list."""
    sample_employee.role.name = "sales"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    assert get_events_by_contract(
        db_session,
        sample_contract.id_contract,
    ) == []


# Test "get_events_by_customer"


@pytest.mark.usefixtures("mock_token_file")
def test_get_events_by_customer_success(
    db_session,
    sample_employee,
    sample_customer,
    sample_event,
):
    """Verify that only events belonging to the customer are returned."""
    sample_employee.role.name = "sales"

    second_contract = Contract(
        total_amount=Decimal("1500.00"),
        outstanding_balance=Decimal("500.00"),
        is_signed=True,
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
        is_signed=True,
        id_customer=other_customer.id_customer,
    )

    db_session.add(other_contract)
    db_session.flush()

    second_event = Event(
        name="Second Event",
        start_datetime=datetime(2027, 2, 10, 10, 0),
        end_datetime=datetime(2027, 2, 10, 18, 0),
        location="Lyon",
        attendees_count=100,
        notes="Second event for the customer",
        id_contract=second_contract.id_contract,
        id_support_employee=None,
    )

    other_event = Event(
        name="Other Event",
        start_datetime=datetime(2027, 3, 10, 10, 0),
        end_datetime=datetime(2027, 3, 10, 18, 0),
        location="Dijon",
        attendees_count=75,
        notes="Event for another customer",
        id_contract=other_contract.id_contract,
        id_support_employee=None,
    )

    db_session.add_all([second_event, other_event])
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    events = get_events_by_customer(
        db_session,
        sample_customer.id_customer,
    )

    assert {event.id_event for event in events} == {
        sample_event.id_event,
        second_event.id_event,
    }
    assert other_event not in events


@pytest.mark.usefixtures("mock_token_file")
def test_get_events_by_customer_no_matches(
    db_session,
    sample_employee,
    sample_customer,
):
    """Verify that a customer without events returns an empty list."""
    sample_employee.role.name = "sales"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    assert get_events_by_customer(
        db_session,
        sample_customer.id_customer,
    ) == []


# Test "get_events_by_support_employee"


@pytest.mark.usefixtures("mock_token_file")
def test_get_events_by_support_employee_success(
    db_session,
    sample_employee,
    sample_event,
):
    """Verify that only events assigned to the employee are returned."""
    sample_employee.role.name = "support"
    sample_event.id_support_employee = sample_employee.id_employee

    second_event = Event(
        name="Second Event",
        start_datetime=datetime(2027, 2, 10, 10, 0),
        end_datetime=datetime(2027, 2, 10, 18, 0),
        location="Lyon",
        attendees_count=100,
        notes="Second assigned event",
        id_contract=sample_event.id_contract,
        id_support_employee=sample_employee.id_employee,
    )

    unassigned_event = Event(
        name="Unassigned Event",
        start_datetime=datetime(2027, 3, 10, 10, 0),
        end_datetime=datetime(2027, 3, 10, 18, 0),
        location="Dijon",
        attendees_count=75,
        notes="Event without support",
        id_contract=sample_event.id_contract,
        id_support_employee=None,
    )

    db_session.add_all([second_event, unassigned_event])
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    events = get_events_by_support_employee(
        db_session,
        sample_employee.id_employee,
    )

    assert {event.id_event for event in events} == {
        sample_event.id_event,
        second_event.id_event,
    }
    assert unassigned_event not in events


@pytest.mark.usefixtures("mock_token_file")
def test_get_events_by_support_employee_no_matches(
    db_session,
    sample_employee,
    sample_event,
):
    """Verify that an employee without assigned events gets an empty list."""
    sample_employee.role.name = "support"
    sample_event.id_support_employee = None
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    assert get_events_by_support_employee(
        db_session,
        sample_employee.id_employee,
    ) == []


# Test ID validation


@pytest.mark.usefixtures("mock_token_file")
@pytest.mark.parametrize(
    "read_operation",
    [
        get_event_by_id,
        get_events_by_contract,
        get_events_by_customer,
        get_events_by_support_employee,
    ],
)
def test_event_reads_validate_ids(
    db_session,
    sample_employee,
    read_operation,
):
    """Verify that event read services reject invalid identifiers."""
    sample_employee.role.name = "sales"
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(TypeError):
        read_operation(db_session, "invalid_id")


# Test event read permissions


@pytest.mark.usefixtures("mock_token_file")
@pytest.mark.parametrize(
    "role_name",
    ["management", "sales", "support"],
)
def test_event_read_allows_all_business_roles(
    db_session,
    sample_employee,
    sample_event,
    role_name,
):
    """Verify that all recognized roles can retrieve events."""
    sample_employee.role.name = role_name
    db_session.flush()

    save_token(create_access_token(sample_employee.id_employee))

    assert get_all_events(db_session) == [sample_event]


@pytest.mark.usefixtures("mock_token_file")
@pytest.mark.parametrize(
    "read_operation",
    READ_OPERATIONS,
    ids=READ_OPERATIONS_IDS,
)
def test_event_reads_require_authentication(
    db_session,
    read_operation,
):
    """Verify that event reading requires authentication."""
    with pytest.raises(PermissionDeniedError):
        read_operation(db_session)


@pytest.mark.usefixtures("mock_token_file")
@pytest.mark.parametrize(
    "read_operation",
    READ_OPERATIONS,
    ids=READ_OPERATIONS_IDS,
)
def test_event_reads_deny_inactive_employee(
    db_session,
    sample_employee,
    read_operation,
):
    """Verify that inactive employees cannot read events."""
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
def test_event_reads_deny_unknown_role(
    db_session,
    sample_employee,
    read_operation,
):
    """Verify that employees with unknown roles cannot read events."""
    # sample_employee has the unknown role "Test Role".
    save_token(create_access_token(sample_employee.id_employee))

    with pytest.raises(PermissionDeniedError):
        read_operation(db_session)


# Test create_event


def test_create_event_success(
    db_session,
    event_data,
):
    """Verify that an authorized sales employee can create an event."""
    event = create_event(db_session, **event_data)

    db_session.flush()

    assert event.id_event is not None
    assert event.name == event_data["name"]
    assert event.start_datetime == event_data["start_datetime"]
    assert event.end_datetime == event_data["end_datetime"]
    assert event.location == event_data["location"]
    assert event.attendees_count == event_data["attendees_count"]
    assert event.id_contract == event_data["id_contract"]
    assert event.notes == event_data["notes"]


def test_create_event_without_notes(
    db_session,
    event_data,
):
    """Verify that event notes are optional."""
    event_data.pop("notes")

    event = create_event(db_session, **event_data)

    assert event.notes is None


def test_create_event_unknown_contract(
    db_session,
    event_data,
):
    """Verify that events cannot reference unknown contracts."""
    event_data["id_contract"] += 1_000_000_000

    with pytest.raises(ValueError, match="does not exist"):
        create_event(db_session, **event_data)


def test_create_event_unsigned_contract(
    db_session,
    signed_owned_contract,
    event_data,
):
    """Verify that an unsigned contract cannot have a new event."""
    signed_owned_contract.is_signed = False
    db_session.flush()

    with pytest.raises(PermissionDeniedError):
        create_event(db_session, **event_data)


def test_create_event_sales_not_owner(
    db_session,
    authenticated_sales,
    signed_owned_contract,
    event_data,
):
    """Verify that sales employees cannot create events for other clients."""
    other_sales = Employee(
        full_name="Other Sales Employee",
        email="other.sales.event@example.com",
        password_hash="test-password-hash",
        is_active=True,
        id_role=authenticated_sales.id_role,
    )
    db_session.add(other_sales)
    db_session.flush()

    signed_owned_contract.customer.id_sales_employee = other_sales.id_employee
    db_session.flush()

    with pytest.raises(PermissionDeniedError):
        create_event(db_session, **event_data)


@pytest.mark.parametrize(
    "start, end",
    [
        (
            datetime(2026, 12, 15, 18, 0),
            datetime(2026, 12, 15, 9, 0),
        ),
        (
            datetime(2026, 12, 15, 9, 0),
            datetime(2026, 12, 15, 9, 0),
        ),
    ],
)
def test_create_event_invalid_dates(
    db_session,
    event_data,
    start,
    end,
):
    """Verify that event end datetime must be after start datetime."""
    event_data["start_datetime"] = start
    event_data["end_datetime"] = end

    with pytest.raises(ValueError):
        create_event(db_session, **event_data)


@pytest.mark.parametrize(
    "field, invalid_value, expected_error",
    [
        ("name", "", ValueError),
        ("start_datetime", "2026-12-15 09:00", TypeError),
        ("end_datetime", None, TypeError),
        ("location", "", ValueError),
        ("attendees_count", -1, ValueError),
        ("attendees_count", True, TypeError),
        ("id_contract", "invalid", TypeError),
    ],
)
def test_create_event_invalid_fields(
    db_session,
    event_data,
    field,
    invalid_value,
    expected_error,
):
    """Verify that invalid event data is rejected."""
    event_data[field] = invalid_value

    with pytest.raises(expected_error):
        create_event(db_session, **event_data)


def test_create_event_management_denied(
    db_session,
    authenticated_manager,
    sample_contract,
):
    """
    Verify that management cannot use the
    sales event-creation permission.
    """
    sample_contract.is_signed = True
    db_session.flush()

    with pytest.raises(PermissionDeniedError):
        create_event(
            db_session,
            name="Management Event",
            start_datetime=datetime(2026, 12, 15, 9, 0),
            end_datetime=datetime(2026, 12, 15, 18, 0),
            location="Paris, France",
            attendees_count=50,
            id_contract=sample_contract.id_contract,
        )


def test_create_event_requires_authentication(
    db_session,
    sample_contract,
    mock_token_file,
):
    """Verify that event creation requires authentication."""
    assert not mock_token_file.exists()

    with pytest.raises(PermissionDeniedError):
        create_event(
            db_session,
            name="Conference",
            start_datetime=datetime(2026, 12, 15, 9, 0),
            end_datetime=datetime(2026, 12, 15, 18, 0),
            location="Paris, France",
            attendees_count=50,
            id_contract=sample_contract.id_contract,
        )


# Test update_event


def test_update_event_success(
    db_session,
    assigned_event,
):
    """Verify that assigned support can update event information."""
    event = update_event(
        db_session,
        assigned_event.id_event,
        name="Updated Conference",
        start_datetime=datetime(2026, 12, 16, 10, 0),
        end_datetime=datetime(2026, 12, 16, 17, 0),
        location="Lyon, France",
        attendees_count=200,
        notes="Updated notes",
    )

    db_session.flush()

    assert event is assigned_event
    assert event.name == "Updated Conference"
    assert event.start_datetime == datetime(2026, 12, 16, 10, 0)
    assert event.end_datetime == datetime(2026, 12, 16, 17, 0)
    assert event.location == "Lyon, France"
    assert event.attendees_count == 200
    assert event.notes == "Updated notes"


def test_update_event_partial(
    db_session,
    assigned_event,
):
    """Verify that omitted event fields remain unchanged."""
    original_name = assigned_event.name
    original_start = assigned_event.start_datetime
    original_end = assigned_event.end_datetime
    original_attendees = assigned_event.attendees_count

    event = update_event(
        db_session,
        assigned_event.id_event,
        location="Marseille, France",
    )

    assert event.location == "Marseille, France"
    assert event.name == original_name
    assert event.start_datetime == original_start
    assert event.end_datetime == original_end
    assert event.attendees_count == original_attendees
    assert event.notes == "Original notes"


def test_update_event_start_datetime_only(
    db_session,
    assigned_event,
):
    """Verify that changing only start datetime preserves end datetime."""
    original_end = assigned_event.end_datetime

    event = update_event(
        db_session,
        assigned_event.id_event,
        start_datetime=datetime(2026, 12, 15, 10, 0),
    )

    assert event.start_datetime == datetime(2026, 12, 15, 10, 0)
    assert event.end_datetime == original_end


def test_update_event_end_datetime_only(
    db_session,
    assigned_event,
):
    """Verify that changing only end datetime preserves start datetime."""
    original_start = assigned_event.start_datetime

    event = update_event(
        db_session,
        assigned_event.id_event,
        end_datetime=datetime(2026, 12, 15, 20, 0),
    )

    assert event.start_datetime == original_start
    assert event.end_datetime == datetime(2026, 12, 15, 20, 0)


def test_update_event_both_datetimes(
    db_session,
    assigned_event,
):
    """Verify that both datetimes can be changed together."""
    event = update_event(
        db_session,
        assigned_event.id_event,
        start_datetime=datetime(2026, 12, 16, 14, 0),
        end_datetime=datetime(2026, 12, 16, 19, 0),
    )

    assert event.start_datetime == datetime(2026, 12, 16, 14, 0)
    assert event.end_datetime == datetime(2026, 12, 16, 19, 0)


@pytest.mark.parametrize(
    "updates",
    [
        {"start_datetime": datetime(2026, 12, 15, 19, 0)},
        {"end_datetime": datetime(2026, 12, 15, 8, 0)},
        {
            "start_datetime": datetime(2026, 12, 16, 18, 0),
            "end_datetime": datetime(2026, 12, 16, 9, 0),
        },
        {
            "start_datetime": datetime(2026, 12, 15, 12, 0),
            "end_datetime": datetime(2026, 12, 15, 12, 0),
        },
    ],
)
def test_update_event_invalid_dates(
    db_session,
    assigned_event,
    updates,
):
    """Verify that inconsistent event dates are rejected."""
    original_start = assigned_event.start_datetime
    original_end = assigned_event.end_datetime

    with pytest.raises(ValueError):
        update_event(
            db_session,
            assigned_event.id_event,
            **updates,
        )

    assert assigned_event.start_datetime == original_start
    assert assigned_event.end_datetime == original_end


def test_update_event_preserves_notes(
    db_session,
    assigned_event,
):
    """Verify that omitted notes remain unchanged."""
    event = update_event(
        db_session,
        assigned_event.id_event,
        location="Paris, France",
    )

    assert event.notes == "Original notes"


def test_update_event_clears_notes(
    db_session,
    assigned_event,
):
    """Verify that explicitly passing None clears existing notes."""
    event = update_event(
        db_session,
        assigned_event.id_event,
        notes=None,
    )

    assert event.notes is None


def test_update_event_replaces_notes(
    db_session,
    assigned_event,
):
    """Verify that existing notes can be replaced."""
    event = update_event(
        db_session,
        assigned_event.id_event,
        notes="New event instructions",
    )

    assert event.notes == "New event instructions"


def test_update_event_unknown_id(
    db_session,
    assigned_event,
):
    """Verify that updating an unknown event is rejected."""
    unknown_id = assigned_event.id_event + 1_000_000_000

    with pytest.raises(ValueError, match="does not exist"):
        update_event(
            db_session,
            unknown_id,
            location="Paris, France",
        )


@pytest.mark.parametrize(
    "field, invalid_value, expected_error",
    [
        ("name", "", ValueError),
        ("location", "", ValueError),
        ("attendees_count", -2, ValueError),
        ("attendees_count", "fifty", TypeError),
        ("start_datetime", "2026-12-15 10:00", TypeError),
    ],
)
def test_update_event_invalid_fields(
    db_session,
    assigned_event,
    field,
    invalid_value,
    expected_error,
):
    """Verify that invalid update values are rejected."""
    with pytest.raises(expected_error):
        update_event(
            db_session,
            assigned_event.id_event,
            **{field: invalid_value},
        )


def test_update_event_unassigned_support_denied(
    db_session,
    assigned_event,
):
    """
    Verify that support cannot update
    an event no longer assigned to them.
    """
    assigned_event.id_support_employee = None
    db_session.flush()

    with pytest.raises(PermissionDeniedError):
        update_event(
            db_session,
            assigned_event.id_event,
            location="Paris, France",
        )


def test_update_event_requires_authentication(
    db_session,
    sample_event,
    mock_token_file,
):
    """Verify that updating events requires authentication."""
    assert not mock_token_file.exists()

    with pytest.raises(PermissionDeniedError):
        update_event(
            db_session,
            sample_event.id_event,
            location="Paris, France",
        )


# Test assign_support_employee_to_event


def test_assign_support_employee_success(
    db_session,
    authenticated_manager,
    sample_event,
    support_employee,
):
    """Verify that management can assign an active support employee."""
    event = assign_support_employee_to_event(
        db_session,
        sample_event.id_event,
        support_employee.id_employee,
    )

    db_session.flush()

    assert event is sample_event
    assert event.id_support_employee == support_employee.id_employee


def test_assign_support_employee_reassignment(
    db_session,
    authenticated_manager,
    sample_event,
    support_employee,
):
    """Verify that an existing support assignment can be replaced."""
    previous_support = Employee(
        full_name="Previous Support Employee",
        email="previous.support@example.com",
        password_hash="test-password-hash",
        is_active=True,
        id_role=support_employee.id_role,
    )
    db_session.add(previous_support)
    db_session.flush()

    sample_event.id_support_employee = previous_support.id_employee
    db_session.flush()

    event = assign_support_employee_to_event(
        db_session,
        sample_event.id_event,
        support_employee.id_employee,
    )

    assert event.id_support_employee == support_employee.id_employee


def test_assign_support_employee_unknown_event(
    db_session,
    authenticated_manager,
    sample_event,
    support_employee,
):
    """Verify that an unknown event cannot receive an assignment."""
    unknown_event_id = sample_event.id_event + 1_000_000_000

    with pytest.raises(ValueError, match="does not exist"):
        assign_support_employee_to_event(
            db_session,
            unknown_event_id,
            support_employee.id_employee,
        )


def test_assign_support_employee_unknown_employee(
    db_session,
    authenticated_manager,
    sample_event,
):
    """Verify that an unknown employee cannot be assigned."""
    unknown_employee_id = 1_000_000_000

    with pytest.raises(ValueError, match="does not exist"):
        assign_support_employee_to_event(
            db_session,
            sample_event.id_event,
            unknown_employee_id,
        )


def test_assign_support_employee_wrong_role(
    db_session,
    authenticated_manager,
    sample_event,
):
    """Verify that management employees cannot be assigned as support."""
    with pytest.raises(ValueError, match="support role"):
        assign_support_employee_to_event(
            db_session,
            sample_event.id_event,
            authenticated_manager.id_employee,
        )


def test_assign_support_employee_inactive(
    db_session,
    authenticated_manager,
    sample_event,
    support_employee,
):
    """Verify that inactive support employees cannot be assigned."""
    support_employee.is_active = False
    db_session.flush()

    with pytest.raises(ValueError, match="inactive"):
        assign_support_employee_to_event(
            db_session,
            sample_event.id_event,
            support_employee.id_employee,
        )


@pytest.mark.parametrize(
    "field, invalid_value",
    [
        ("event_id", 0),
        ("event_id", "invalid"),
        ("id_support_employee", -1),
        ("id_support_employee", True),
    ],
)
def test_assign_support_employee_invalid_ids(
    db_session,
    authenticated_manager,
    sample_event,
    support_employee,
    field,
    invalid_value,
):
    """Verify that invalid IDs are rejected."""
    data = {
        "event_id": sample_event.id_event,
        "id_support_employee": support_employee.id_employee,
    }
    data[field] = invalid_value

    with pytest.raises((TypeError, ValueError)):
        assign_support_employee_to_event(db_session, **data)


def test_assign_support_employee_sales_denied(
    db_session,
    authenticated_sales,
    sample_event,
):
    """Verify that sales employees cannot assign support staff."""
    with pytest.raises(PermissionDeniedError):
        assign_support_employee_to_event(
            db_session,
            sample_event.id_event,
            authenticated_sales.id_employee,
        )


def test_assign_support_employee_requires_authentication(
    db_session,
    sample_event,
    mock_token_file,
):
    """Verify that support assignment requires authentication."""
    assert not mock_token_file.exists()

    with pytest.raises(PermissionDeniedError):
        assign_support_employee_to_event(
            db_session,
            sample_event.id_event,
            1,
        )
