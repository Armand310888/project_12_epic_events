"""Define the main CLI entry point and register command groups."""

import click

from epic_events.cli.auth import auth
from epic_events.cli.contracts import contracts
from epic_events.cli.customers import customers
from epic_events.cli.employees import employees
from epic_events.cli.events import events


@click.group()
def cli():
    """Epic Events command-line interface."""


cli.add_command(auth)
cli.add_command(customers)
cli.add_command(employees)
cli.add_command(contracts)
cli.add_command(events)


if __name__ == "__main__":
    cli()
