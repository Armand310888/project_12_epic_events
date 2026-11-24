"""Define CLI commands for contract management"""

from decimal import Decimal

import click

from epic_events.cli.display import display_contracts
from epic_events.database import session_factory
from epic_events.security.authorizations import (
    Permission,
    PermissionDeniedError,
    require_general_permission,
)
from epic_events.services.auth_service import get_current_employee
from epic_events.services.contract_service import (
    create_contract as service_create_contract,
)
from epic_events.services.contract_service import get_contracts
from epic_events.services.customer_service import (
    get_customer_by_id,
)


@click.group()
def contracts():
    """Manage contracts"""


@contracts.command(name="list")
@click.option(
    "--customer",
    type=str,
    default=None,
    help="Filter contracts by customer name.",
)
@click.option(
    "--company",
    type=str,
    default=None,
    help="Filter contracts by company name.",
)
@click.option(
    "--unsigned",
    is_flag=True,
    help="Show only unsigned contracts."
)
@click.option(
    "--unpaid",
    is_flag=True,
    help="Show only contracts with an outstanding balance."
)
def list_contracts(
    customer: str | None,
    company: str | None,
    unsigned: bool,
    unpaid: bool
) -> None:
    """List contracts with optional filters. """
    try:
        with session_factory() as session:
            contracts_list = get_contracts(
                session,
                customer_name=customer,
                company_name=company,
                unsigned=unsigned,
                unpaid=unpaid,
            )

            display_contracts(contracts_list)

    except (ValueError, TypeError, PermissionDeniedError) as exception:
        raise click.ClickException(str(exception)) from exception


@contracts.command(name="create")
def create_contract() -> None:
    """Create a new contract."""
    try:
        with session_factory() as session:
            employee = get_current_employee(session)
            require_general_permission(
                employee,
                Permission.CONTRACT_CREATE,
            )

    except PermissionDeniedError as exception:
        raise click.ClickException(str(exception)) from exception

    total_amount = click.prompt(
        "Total amount",
        type=Decimal,
    )
    outstanding_balance = click.prompt(
        "Outstanding balance",
        type=Decimal,
    )
    customer_id = click.prompt(
        "Customer ID",
        type=int,
    )

    is_signed = click.confirm(
        "Is the contract signed?",
        default=False,
    )

    try:
        with session_factory() as session:
            contract = service_create_contract(
                session,
                total_amount,
                outstanding_balance,
                customer_id,
                is_signed,
            )

            session.commit()

            contract_id = contract.id_contract
            customer = get_customer_by_id(session, customer_id)
            customer_name = customer.full_name

    except (ValueError, TypeError, PermissionDeniedError) as exception:
        raise click.ClickException(str(exception)) from exception

    click.echo(
        f"Contract n°{contract_id} "
        f"for customer '{customer_name}' created successfully.")
