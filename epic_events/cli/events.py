"""Define CLI commands for event management."""

import click

from epic_events.cli.display import display_events
from epic_events.database import session_factory
from epic_events.security.authorizations import (
    Permission,
    PermissionDeniedError,
    require_general_permission,
)
from epic_events.services.auth_service import get_current_employee
from epic_events.services.event_service import (
    create_event as service_create_event,
)
from epic_events.services.event_service import (
    get_events,
)


@click.group()
def events():
    """Manage events."""


@events.command(name="list")
@click.option(
    "--unassigned",
    is_flag=True,
    help="Show only events with no support employee."
)
@click.option(
    "--upcoming",
    is_flag=True,
    help="Show only upcoming events."
)
@click.option(
    "--past",
    is_flag=True,
    help="Show only past events."
)
@click.option(
    "--contract-id",
    type=int,
    default=None,
    help="Filter events by contract ID."
)
@click.option(
    "--customer",
    type=str,
    default=None,
    help="Filter events by customer name."
)
@click.option(
    "--support-employee",
    type=str,
    default=None,
    help="Filter events by support employee name"
)
def list_events(
    unassigned: bool,
    upcoming: bool,
    past: bool,
    contract_id: int | None,
    customer: str | None,
    support_employee: str | None,
) -> None:
    """List events with optional filters."""
    try:
        with session_factory() as session:
            events_list = get_events(
                session,
                unassigned=unassigned,
                upcoming=upcoming,
                past=past,
                contract_id=contract_id,
                customer_name=customer,
                support_employee_name=support_employee
            )

            display_events(events_list)

    except (ValueError, TypeError, PermissionDeniedError) as exception:
        raise click.ClickException(str(exception)) from exception


@events.command(name="create")
def create_event() -> None:
    """Create a new event."""
    try:
        with session_factory() as session:
            employee = get_current_employee(session)
            require_general_permission(
                employee,
                Permission.EVENT_CREATE,
            )

    except PermissionDeniedError as exception:
        raise click.ClickException(str(exception)) from exception

    name = click.prompt("Name")

    start_datetime = click.prompt(
        "Start datetime",
        type=click.DateTime(
            formats=["%Y-%m-%d %H:%M"]
        ),
    )

    end_datetime = click.prompt(
        "End datetime",
        type=click.DateTime(
            formats=["%Y-%m-%d %H:%M"]
        ),
    )
    location = click.prompt("Location")

    attendees_count = click.prompt(
        "Attendees count",
        type=int,
    )

    notes = click.prompt(
        "Notes",
        default="",
        show_default=False,
    )

    notes = notes.strip() or None

    id_contract = click.prompt(
        "ID contract",
        type=int,
    )

    try:
        with session_factory() as session:
            event = service_create_event(
                session,
                name,
                start_datetime,
                end_datetime,
                location,
                attendees_count,
                id_contract,
                notes
            )

            session.commit()

            event_name = event.name

    except (ValueError, TypeError, PermissionDeniedError) as exception:
        raise click.ClickException(str(exception)) from exception

    click.echo(f"Event '{event_name}' created successfully.")
