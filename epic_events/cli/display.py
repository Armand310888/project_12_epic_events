"""Provide Rich-based formatting and display utilities for the CLI."""

from rich.console import Console
from rich.table import Table

from epic_events.models import Contract, Customer

console = Console()


def display_customers(customers: list[Customer]) -> None:
    """Display customers in a formatted table."""
    if not customers:
        console.print("No customers found.")
        return

    table = Table(title="Customers")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Email")
    table.add_column("Phone number")
    table.add_column("Company")

    for customer in customers:
        table.add_row(
            customer.id_customer,
            customer.full_name,
            customer.email,
            customer.phone_number,
            customer.company or "-"
        )

    console.print(table)


def display_contracts(contracts: list[Contract]) -> None:
    """Display contracts in a formatted table."""
    if not contracts:
        console.print("No contracts found.")
        return

    table = Table(title="Contracts")
    table.add_column("ID")
    table.add_column("Customer")
    table.add_column("Company")
    table.add_column("Is signed")
    table.add_column("Amount")
    table.add_column("Outstanding balance")
    table.add_column("Creation datetime")

    for contract in contracts:
        table.add_row(
            str(contract.id_contract),
            contract.customer.full_name,
            contract.customer.company or "-",
            "Yes" if contract.is_signed else "No",
            str(contract.total_amount),
            str(contract.outstanding_balance),
            str(contract.creation_datetime),
        )

    console.print(table)
