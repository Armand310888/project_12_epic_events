"""Provide Rich-based formatting and display utilities for the CLI."""

from rich.console import Console
from rich.table import Table

from epic_events.models import Contract, Customer, Event

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
            str(customer.id_customer),
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
            contract.customer.sales_employee.full_name,
        )

    console.print(table)


def display_events(events: list[Event]) -> None:
    """Display events in a formatted table."""
    if not events:
        console.print("No events found.")
        return

    table = Table(title="Events")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Start datetime")
    table.add_column("End datetime")
    table.add_column("Location")
    table.add_column("Attendees count")
    table.add_column("Notes")
    table.add_column("ID Contract")
    table.add_column("ID support employee")
    table.add_column("Support employee name")

    for event in events:
        table.add_row(
            str(event.id_event),
            event.name,
            str(event.start_datetime),
            str(event.end_datetime),
            event.location,
            str(event.attendees_count),
            event.notes or "-",
            str(event.id_contract),
            str(event.support_employee.id_employee)
            if event.id_support_employee is not None else "-",
            event.support_employee.full_name
            if event.support_employee is not None else "-",
        )

    console.print(table)
