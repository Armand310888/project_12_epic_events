"""Define CLI commands for employee management."""

import click

from epic_events.database import session_factory
from epic_events.security.authorizations import (
    Permission,
    PermissionDeniedError,
    require_general_permission,
)
from epic_events.services.auth_service import get_current_employee
from epic_events.services.employee_service import (
    create_employee as service_create_employee,
)
from epic_events.services.employee_service import (
    get_role_by_name,
)


@click.group()
def employees():
    """Manage employees."""


@employees.command(name="create")
def create_employee() -> None:
    """Create a new employee."""
    try:
        with session_factory() as session:
            employee = get_current_employee(session)
            require_general_permission(
                employee,
                Permission.EMPLOYEE_CREATE,
            )

    except PermissionDeniedError as exception:
        raise click.ClickException(str(exception)) from exception

    full_name = click.prompt("Full name")
    email = click.prompt("Email")
    password = click.prompt(
        "Password",
        hide_input=True,
        confirmation_prompt=True,
    )
    role_name = click.prompt("Role (management, sales, support)")

    try:
        with session_factory() as session:
            role = get_role_by_name(session, role_name)

            if role is None:
                raise click.ClickException("Unknown role.")

            employee = service_create_employee(
                session,
                full_name,
                email,
                password,
                role.id_role,
            )

            session.commit()

            employee_name = employee.full_name

    except (ValueError, TypeError, PermissionDeniedError) as exception:
        raise click.ClickException(str(exception)) from exception

    click.echo(f"Employee '{employee_name}' created successfully.")
