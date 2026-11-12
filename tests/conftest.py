"""Configure shared fixtures for database integration tests."""

import os
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from epic_events.models import Contract, Customer, Employee, Role
from epic_events.security import token_storage
from epic_events.security.passwords import hash_password

TEST_EMPLOYEE_PASSWORD = "TestPassword123!"
TEST_EMPLOYEE_PASSWORD_HASH = hash_password(TEST_EMPLOYEE_PASSWORD)


@pytest.fixture
def test_employee_password():
    """Provide the password used by the sample employee fixture."""
    return TEST_EMPLOYEE_PASSWORD


@pytest.fixture(scope="session")
def test_engine():
    """Provide a dedicated MySQL test engine
    and dispose of it after the test session.
    """
    password = os.environ["EPIC_EVENTS_TEST_DB_PASSWORD"]

    url = URL.create(
        drivername="mysql+pymysql",
        username="epic_events_test_app",
        password=password,
        host="172.29.16.1",
        port=3306,
        database="epic_events_test",
    )

    test_engine = create_engine(url, echo=True)

    yield test_engine

    test_engine.dispose()


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    """Provide a session factory bound to the test database."""
    return sessionmaker(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(test_engine, test_session_factory):
    """Provide an isolated database session for each test."""
    with test_engine.connect() as connection:
        transaction = connection.begin()

        try:
            with test_session_factory(
                bind=connection,
                join_transaction_mode="create_savepoint",
            ) as session:
                yield session
        finally:
            transaction.rollback()


@pytest.fixture
def sample_role(db_session):
    """Create a role for integration tests."""
    role = Role(name="Test Role")
    db_session.add(role)
    db_session.flush()
    return role


@pytest.fixture
def sample_employee(db_session, sample_role):
    """Create an employee for integration tests."""
    employee = Employee(
        full_name="Test Employee",
        email="testemployee@example.com",
        password_hash=TEST_EMPLOYEE_PASSWORD_HASH,
        id_role=sample_role.id_role,
    )
    db_session.add(employee)
    db_session.flush()

    return employee


@pytest.fixture
def sample_customer(db_session, sample_employee):
    """Create a customer for integration tests."""
    customer = Customer(
        full_name="Test Customer",
        email="testcustomer@example.com",
        phone_number="0102030405",
        id_sales_employee=sample_employee.id_employee
    )
    db_session.add(customer)
    db_session.flush()

    return customer


@pytest.fixture
def sample_contract(db_session, sample_customer):
    """Create a contract for integration tests."""
    contract = Contract(
        total_amount=Decimal("1000.00"),
        outstanding_balance=Decimal("500.00"),
        id_customer=sample_customer.id_customer,
    )

    db_session.add(contract)
    db_session.flush()

    return contract


@pytest.fixture
def mock_token_file(monkeypatch, tmp_path):
    """Configure a temporary token storage file for tests."""
    token_file = tmp_path / "token"
    monkeypatch.setattr(token_storage, "TOKEN_FILE", token_file)
    return token_file
