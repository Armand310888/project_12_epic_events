"""Provide Rich-based formatting and display utilities for the CLI."""

from rich.console import Console
from rich.table import Table

from epic_events.models import Customer

console = Console()


def display_customers(customers: list[Customer]) -> None:
    """Display customers in a formatted table."""
    if not customers:
        console.print("No customers found.")
        return

    table = Table(title="Customers")
    table.add_column("Name")
    table.add_column("Email")
    table.add_column("Phone number")
    table.add_column("Company")

    for customer in customers:
        table.add_row(
            customer.full_name,
            customer.email,
            customer.phone_number,
            customer.company or "-"
        )

    console.print(table)
