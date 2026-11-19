import click

from epic_events.database import session_factory
from epic_events.services.customer_service import (
    get_all_customers,
)


@click.group()
def customers():
    """Manage customers."""


@customers.command(name="list")
def list_customers():
    """List all customers."""
    with session_factory() as session:
        customers = get_all_customers(session)

        for customer in customers:
            click.echo(customer.full_name)
