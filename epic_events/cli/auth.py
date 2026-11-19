import click

from epic_events.database import session_factory
from epic_events.services.auth_service import (
    AlreadyAuthenticatedError,
    login_employee,
)


@click.group()
def auth():
    """Manage employee authentication."""


@auth.command(name="login")
def login():
    """
    Authenticate an employee using their email and password.

    Prompt for credentials without displaying the password.
    """
    email = click.prompt("Email")
    password = click.prompt(
        "Password",
        hide_input=True,
    )

    try:
        with session_factory() as session:
            employee = login_employee(
                session,
                email,
                password,
            )

            if employee is not None:
                employee_name = employee.full_name

    except AlreadyAuthenticatedError as exception:
        raise click.ClickException(str(exception)) from exception

    if employee is None:
        raise click.ClickException("Invalid email or password.")

    click.echo(f"Welcome, {employee_name}!")
