"""Define CLI commands for customer management."""

import click

from epic_events.cli.display import display_customers
from epic_events.database import session_factory
from epic_events.security.authorizations import (
    Permission,
    PermissionDeniedError,
    require_general_permission,
)
from epic_events.services.auth_service import get_current_employee
from epic_events.services.customer_service import (
    create_customer as service_create_customer,
)
from epic_events.services.customer_service import (
    get_all_customers,
)


@click.group()
def customers():
    """Manage customers."""


@customers.command(name="list")
def list_customers():
    """List all customers."""
    try:
        with session_factory() as session:
            customers = get_all_customers(session)
            display_customers(customers)

    except PermissionDeniedError as exception:
        raise click.ClickException(str(exception)) from exception


@customers.command(name="create")
def create_customer() -> None:
    """Create a new customer."""
    try:
        with session_factory() as session:
            employee = get_current_employee(session)
            require_general_permission(
                employee,
                Permission.CUSTOMER_CREATE)

    except PermissionDeniedError as exception:
        raise click.ClickException(str(exception)) from exception

    full_name = click.prompt("Full name")
    email = click.prompt("Email")
    phone_number = click.prompt("Phone number")
    company = click.prompt(
        "Company",
        default="",
        show_default=False,
    )
    company = company or None

    try:
        with session_factory() as session:
            customer = service_create_customer(
                session,
                full_name,
                email,
                phone_number,
                company,
            )

            session.commit()

            customer_name = customer.full_name

    except (ValueError, TypeError, PermissionDeniedError) as exception:
        raise click.ClickException(str(exception)) from exception

    click.echo(f"Customer '{customer_name}' created successfully.")
