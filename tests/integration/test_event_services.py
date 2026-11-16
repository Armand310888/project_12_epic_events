
"""Integration tests for event management services."""

from datetime import datetime
from decimal import Decimal

import pytest

from epic_events.models import Contract, Customer, Event
from epic_events.security.authorizations import PermissionDeniedError
from epic_events.security.token_storage import save_token
from epic_events.security.tokens import create_access_token
from epic_events.services.event_service import (
    get_all_events,
    get_event_by_id,
    get_events_by_contract,
    get_events_by_customer,
    get_events_by_support_employee,
    get_events_without_support,
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
