
"""
Provide event management services
with authentication and authorization.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from epic_events.models import Contract, Customer, Employee, Event
from epic_events.security.authorizations import (
    Permission,
    require_event_create_permission,
    require_event_update_permission,
    require_general_permission,
)
from epic_events.services.auth_service import get_current_employee
from epic_events.services.contract_service import get_contract_by_id
from epic_events.services.employee_service import get_employee_by_id
from epic_events.services.validators import (
    validate_address,
    validate_attendees_count,
    validate_event_name,
    validate_full_name,
    validate_id,
    validate_notes_text,
    validate_start_before_end_datetime,
)


class _UnsetType:
    """Represent a function argument that was not provided."""


_UNSET = _UnsetType()


def get_events(
    session: Session,
    unassigned: bool = False,
    upcoming: bool = False,
    past: bool = False,
    contract_id: int | None = None,
    customer_name: str | None = None,
    support_employee_name: str | None = None,
) -> list[Event]:
    """
    Retrieve events matching optional filters.

    Require the EVENT_READ.

    Allow filtering by assignment status, upcoming or past status,
    contract ID, customer name, and support employee name.

    Return matching events, or an empty list if none exist.
    Raise PermissionDeniedError if access is unauthorized.
    Raise TypeError or ValueError if a filter is invalid.
    """
    employee = get_current_employee(session)
    require_general_permission(employee, Permission.EVENT_READ)

    statement = select(Event)

    if not isinstance(unassigned, bool):
        raise TypeError("'unassigned' must be a boolean.")

    if unassigned:
        statement = statement.where(Event.id_support_employee.is_(None))

    if not isinstance(upcoming, bool):
        raise TypeError("'upcoming' must be a boolean.")

    if not isinstance(past, bool):
        raise TypeError("'past' must be a boolean.")

    if upcoming and past:
        raise ValueError(
            "Filters 'upcoming' and 'past' cannot be combined."
        )
    now = datetime.now()

    if upcoming:
        statement = statement.where(Event.start_datetime >= now)

    if past:
        statement = statement.where(Event.end_datetime < now)

    if contract_id is not None:
        contract_id = validate_id(contract_id)
        statement = statement.where(Event.id_contract == contract_id)

    if customer_name is not None:
        statement = statement.join(
            Contract,
            Event.id_contract == Contract.id_contract
        ).join(
            Customer,
            Contract.id_customer == Customer.id_customer,
        )

        customer_name = validate_full_name(customer_name)

        statement = statement.where(
            Customer.full_name.ilike(f"%{customer_name}%")
        )

    if support_employee_name is not None:
        statement = statement.join(
            Employee,
            Event.id_support_employee == Employee.id_employee,
        )

        support_employee_name = validate_full_name(support_employee_name)

        statement = statement.where(
            Employee.full_name.ilike(
                f"%{support_employee_name}%"
            )
        )

    return list(session.scalars(statement).all())


def get_event_by_id(
    session: Session,
    event_id: int,
) -> Event | None:
    """
    Retrieve an event by ID for an authenticated and authorized employee.

    Require the EVENT_READ permission before querying the database.
    Validate the event ID before executing the query.

    Return the event if found, or None if no event matches the ID.
    Raise TypeError or ValueError if the event ID is invalid.
    Raise PermissionDeniedError if access is unauthorized.
    """
    employee = get_current_employee(session)
    require_general_permission(employee, Permission.EVENT_READ)

    event_id = validate_id(event_id)

    return session.get(Event, event_id)


def create_event(
    session: Session,
    name: str,
    start_datetime: datetime,
    end_datetime: datetime,
    location: str,
    attendees_count: int,
    id_contract: int,
    notes: str | None = None,
) -> Event:
    """
    Create a new event associated with an existing contract.

    Require an authenticated employee authorized to create an event
    for the specified contract.

    Validate the event name, start and end datetimes, location,
    attendees count, and optional notes.

    Ensure that the associated contract exists and that the event
    dates are chronologically consistent.

    Add the new event to the session without committing the transaction.

    Return the newly created Event instance.

    Raise PermissionDeniedError if the employee is unauthorized.
    Raise ValueError if the contract does not exist or the data is invalid.
    Raise TypeError if a provided value has an invalid type.
    """
    current_employee = get_current_employee(session)

    id_contract = validate_id(id_contract)
    contract = get_contract_by_id(session, id_contract)
    if contract is None:
        raise ValueError(f"Contract with ID {id_contract} does not exist.")

    require_event_create_permission(current_employee, contract)

    name = validate_event_name(name)

    start_datetime, end_datetime = validate_start_before_end_datetime(
        start_datetime,
        end_datetime
    )

    location = validate_address(location)

    attendees_count = validate_attendees_count(attendees_count)

    if notes is not None:
        notes = validate_notes_text(notes)

    event = Event(
        name=name,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        location=location,
        attendees_count=attendees_count,
        notes=notes,
        id_contract=id_contract,
    )

    session.add(event)
    return event


def update_event(
    session: Session,
    event_id: int,
    name: str | None = None,
    start_datetime: datetime | None = None,
    end_datetime: datetime | None = None,
    location: str | None = None,
    attendees_count: int | None = None,
    notes: str | None | _UnsetType = _UNSET,
) -> Event:
    """
    Update an existing event's information.

    Require an authenticated employee authorized to modify the event.

    Retrieve the event and validate the provided fields, including
    the chronological consistency of its start and end datetimes.

    Update only the specified fields, preserving all omitted values.
    Allow existing notes to be cleared by explicitly passing None.

    Keep the event associated with its original contract.

    Apply changes without committing the transaction.

    Return the updated Event instance.

    Raise PermissionDeniedError if the employee is unauthorized.
    Raise ValueError if the event does not exist or the data is invalid.
    Raise TypeError if a provided value has an invalid type.
    """
    current_employee = get_current_employee(session)

    event_id = validate_id(event_id)
    event = get_event_by_id(session, event_id)
    if event is None:
        raise ValueError(f"Event with ID {event_id} does not exist.")

    require_event_update_permission(current_employee, event)

    if name is not None:
        name = validate_event_name(name)

    if start_datetime is not None or end_datetime is not None:
        new_start = (
            start_datetime
            if start_datetime is not None
            else event.start_datetime
        )

        new_end = (
            end_datetime
            if end_datetime is not None
            else event.end_datetime
        )

        new_start, new_end = validate_start_before_end_datetime(
            new_start,
            new_end,
        )

    if location is not None:
        location = validate_address(location)

    if attendees_count is not None:
        attendees_count = validate_attendees_count(attendees_count)

    if notes is not _UNSET and notes is not None:
        notes = validate_notes_text(notes)

    if name is not None:
        event.name = name

    if start_datetime is not None:
        event.start_datetime = new_start

    if end_datetime is not None:
        event.end_datetime = new_end

    if location is not None:
        event.location = location

    if attendees_count is not None:
        event.attendees_count = attendees_count

    if notes is not _UNSET:
        event.notes = notes

    return event


def assign_support_employee_to_event(
    session: Session,
    event_id: int,
    id_support_employee: int,
) -> Event:
    """
    Assign an active support employee to an existing event.

    Require an authenticated employee with the EVENT_ASSIGN_SUPPORT
    permission.

    Validate the event and employee IDs, and ensure that both
    entities exist.

    Verify that the assigned employee has the support role
    and is currently active.

    Update the event's support employee without committing
    the transaction.

    Return the updated Event instance.

    Raise PermissionDeniedError if the employee is unauthorized.
    Raise ValueError if the event or employee does not exist,
    or if the assigned employee is not eligible.
    Raise TypeError or ValueError if an ID is invalid.
    """
    current_employee = get_current_employee(session)
    require_general_permission(
        current_employee,
        Permission.EVENT_ASSIGN_SUPPORT
    )

    event_id = validate_id(event_id)
    id_support_employee = validate_id(id_support_employee)

    event = get_event_by_id(session, event_id)
    if event is None:
        raise ValueError(f"Event with ID {event_id} does not exist.")

    support_employee = get_employee_by_id(session, id_support_employee)
    if support_employee is None:
        raise ValueError(
            f"Employee with ID {id_support_employee} does not exist."
        )
    if support_employee.role.name != "support":
        raise ValueError("Assigned employee must have the support role.")

    if not support_employee.is_active:
        raise ValueError("Cannot assign an inactive employee to an event.")

    event.id_support_employee = id_support_employee

    return event
