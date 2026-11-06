"""Integration tests for database connectivity and transaction isolation."""

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, OperationalError

from epic_events.models import Contract, Employee, Event, Role


def test_database_connection(db_session):
    """Verify that the test database is accessible."""
    result = db_session.execute(text("SELECT DATABASE()"))

    assert result.scalar_one() == "epic_events_test"


class TestDatabaseRollback:
    """Verify automatic transaction rollback between consecutive tests.

    These tests are intentionally order-dependent:
    the first creates a role, and the second verifies that the
    db_session fixture rolled back the insertion.

    Run both tests in their declaration order.
    """

    def test_role_creation(self, db_session, sample_role):
        """Verify that a role can be created and retrieved."""
        db_session.commit()

        statement = select(Role).where(Role.id_role == sample_role.id_role)
        result = db_session.scalar(statement)

        assert result is not None
        assert result.name == sample_role.name

    def test_role_creation_is_rolled_back(self, db_session):
        """Verify that the previous test's role was rolled back."""
        statement = select(Role).where(Role.name == "Test Role")
        result = db_session.scalar(statement)

        assert result is None


def test_role_name_must_be_unique(db_session, sample_role):
    """Verify that duplicate role names are rejected."""
    test_role = Role(name=sample_role.name)
    db_session.add(test_role)

    with pytest.raises(IntegrityError) as exception_info:
        db_session.flush()

    assert exception_info.value.orig.args[0] == 1062


def test_employee_requires_existing_role(db_session):
    """Verify that employees cannot reference nonexistent roles."""
    employee = Employee(
        full_name="Test Employee",
        email="testemployee@example.com",
        password_hash="fake_hash_for_testing",
        id_role=1,
    )

    statement = select(Role).where(Role.id_role == 1)
    result = db_session.scalar(statement)

    assert result is None

    db_session.add(employee)

    with pytest.raises(IntegrityError) as exception_info:
        db_session.flush()

    assert exception_info.value.orig.args[0] == 1452
    assert "id_role" in exception_info.value.orig.args[1]


def test_contract_balance_cannot_exceed_total(
    db_session,
    sample_customer,
):
    """Verify that outstanding balance cannot exceed contract total."""
    contract_amount = Decimal("1000.00")

    contract = Contract(
        total_amount=contract_amount,
        outstanding_balance=contract_amount * 2,
        id_customer=sample_customer.id_customer,
    )

    db_session.add(contract)

    with pytest.raises(OperationalError) as exception_info:
        db_session.flush()

    assert exception_info.value.orig.args[0] == 3819
    assert (
        "ck_contract_outstanding_balance_equal_or_less_than_total_amount"
        in exception_info.value.orig.args[1]
    )


def test_event_end_date_must_follow_start_date(db_session, sample_contract):
    """Verify that an event cannot end before it starts."""
    event = Event(
        name="Test Event",
        start_datetime=datetime(2026, 11, 6, 14, 30, 0),
        end_datetime=datetime(2025, 11, 6, 14, 30, 0),
        location="Adresse de test",
        attendees_count=10,
        id_contract=sample_contract.id_contract,
    )

    db_session.add(event)

    with pytest.raises(OperationalError) as exception_info:
        db_session.flush()

    assert exception_info.value.orig.args[0] == 3819
    assert (
        "ck_event_end_datetime_later_than_start_datetime"
        in exception_info.value.orig.args[1]
    )


def test_contract_balance_can_equal_total(db_session, sample_customer):
    """Verify that outstanding balance may equal contract total."""
    contract_amount = Decimal("1000.00")

    contract = Contract(
        total_amount=contract_amount,
        outstanding_balance=contract_amount,
        id_customer=sample_customer.id_customer,
    )

    db_session.add(contract)
    db_session.commit()

    statement = select(Contract).where(Contract.id_contract == contract.id_contract)
    result = db_session.scalar(statement)

    assert result is not None
    assert result.id_contract == contract.id_contract
    assert result.total_amount == contract_amount
    assert result.outstanding_balance == contract_amount
