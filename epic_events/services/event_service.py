
"""
Provide event management services
with authentication and authorization.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from epic_events.models import Contract, Event
from epic_events.security.authorizations import (
    Permission,
    require_general_permission,
)
from epic_events.services.auth_service import get_current_employee
from epic_events.services.validators import validate_id


def get_all_events(session: Session) -> list[Event]:
    """
    Retrieve all events for an authenticated and authorized employee.

    Require the EVENT_READ permission before querying the database.

    Return all events, or an empty list if none exist.
    Raise PermissionDeniedError if access is unauthorized.
    """
    employee = get_current_employee(session)
    require_general_permission(employee, Permission.EVENT_READ)

    statement = select(Event)
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


def get_events_without_support(session: Session) -> list[Event]:
    """
    Retrieve all events without an assigned support employee.

    Require the EVENT_READ permission before querying the database.

    Return events with no support employee assigned,
    or an empty list if none match.
    Raise PermissionDeniedError if access is unauthorized.
    """
    employee = get_current_employee(session)
    require_general_permission(employee, Permission.EVENT_READ)

    statement = select(Event).where(Event.id_support_employee.is_(None))
    return list(session.scalars(statement).all())


def get_events_by_contract(
    session: Session,
    contract_id: int,
) -> list[Event] | None:
    """
    Retrieve all events associated with a specific contract.

    Require the EVENT_READ permission before querying the database.
    Validate the contract ID before executing the query.

    Return matching events, or an empty list if none exist.
    Raise TypeError or ValueError if the contract ID is invalid.
    Raise PermissionDeniedError if access is unauthorized.
    """
    employee = get_current_employee(session)
    require_general_permission(employee, Permission.EVENT_READ)

    contract_id = validate_id(contract_id)

    statement = (
        select(Event).join(Contract).where(Contract.id_contract == contract_id)
    )
    return list(session.scalars(statement).all())


def get_events_by_customer(
    session: Session,
    customer_id: int,
) -> list[Event]:
    """
    Retrieve all events associated with a specific customer.

    Require the EVENT_READ permission before querying the database.
    Validate the customer ID before executing the query.

    Return matching events, or an empty list if none exist.
    Raise TypeError or ValueError if the customer ID is invalid.
    Raise PermissionDeniedError if access is unauthorized.
    """
    employee = get_current_employee(session)
    require_general_permission(employee, Permission.EVENT_READ)

    customer_id = validate_id(customer_id)

    statement = (
        select(Event).join(Contract).where(Contract.id_customer == customer_id)
    )
    return list(session.scalars(statement).all())


def get_events_by_support_employee(
    session: Session,
    support_employee_id: int,
) -> list[Event]:
    """
    Retrieve all events assigned to a specific support employee.

    Require the EVENT_READ permission before querying the database.
    Validate the support employee ID before executing the query.

    Return matching events, or an empty list if none exist.
    Raise TypeError or ValueError if the employee ID is invalid.
    Raise PermissionDeniedError if access is unauthorized.
    """
    employee = get_current_employee(session)
    require_general_permission(employee, Permission.EVENT_READ)

    support_employee_id = validate_id(support_employee_id)

    statement = (
        select(Event).where(Event.id_support_employee == support_employee_id)
    )
    return list(session.scalars(statement).all())
