import click

from epic_events.cli.auth import auth
from epic_events.cli.customers import customers


@click.group()
def cli():
    """Epic Events command-line interface."""


cli.add_command(auth)
cli.add_command(customers)


if __name__ == "__main__":
    cli()
