"""Unit tests for role-based permissions and access control."""

from unittest.mock import Mock

import pytest

from epic_events.security.authorizations import (
    Permission,
    PermissionDeniedError,
    require_contract_update_permission,
    require_customer_update_permission,
    require_event_create_permission,
    require_event_update_permission,
    require_general_permission,
)

# Test "require_general_permission"


def test_require_general_permission_grants_authorized_access():
    """
    Verify that an active employee with the required permission
    is authorized.
    """
    employee = Mock()
    employee.is_active = True
    employee.role.name = "management"

    permission = Permission.EMPLOYEE_CREATE

    result = require_general_permission(employee, permission)

    assert result is None


def test_require_general_permission_denies_unauthorized_access():
    """
    Verify that an employee lacking the required permission
    is denied access.
    """
    employee = Mock()
    employee.is_active = True
    employee.role.name = "sales"

    permission = Permission.EMPLOYEE_CREATE

    with pytest.raises(PermissionDeniedError):
        require_general_permission(employee, permission)


def test_require_general_permission_denies_unknown_role():
    """Verify that an employee with an unknown role is denied access."""
    employee = Mock()
    employee.is_active = True
    employee.role.name = "admin"

    permission = Permission.EMPLOYEE_CREATE

    with pytest.raises(PermissionDeniedError):
        require_general_permission(employee, permission)


def test_require_general_permission_denies_inactive_employee():
    """
    Verify that an inactive employee is denied access
    despite having the required permission.
    """
    employee = Mock()
    employee.is_active = False
    employee.role.name = "management"

    permission = Permission.EMPLOYEE_CREATE

    with pytest.raises(PermissionDeniedError):
        require_general_permission(employee, permission)


def test_require_general_permission_denies_missing_employee():
    """Verify that access is denied when no employee is provided."""
    employee = None

    permission = Permission.EMPLOYEE_CREATE

    with pytest.raises(PermissionDeniedError):
        require_general_permission(employee, permission)


def test_require_general_permission_denies_missing_role():
    """Verify that an employee without an assigned role is denied access."""
    employee = Mock()
    employee.is_active = True
    employee.role = None

    permission = Permission.EMPLOYEE_CREATE

    with pytest.raises(PermissionDeniedError):
        require_general_permission(employee, permission)


# Test require_customer_update_permission


def test_customer_update_allows_assigned_sales_employee():
    """Allow a sales employee to update their assigned customer."""
    employee = Mock()
    employee.is_active = True
    employee.role.name = "sales"
    employee.id_employee = 1

    customer = Mock()
    customer.id_sales_employee = 1

    assert require_customer_update_permission(employee, customer) is None


def test_customer_update_denies_unassigned_sales_employee():
    """Deny a sales employee access to another employee's customer."""
    employee = Mock()
    employee.is_active = True
    employee.role.name = "sales"
    employee.id_employee = 1

    customer = Mock()
    customer.id_sales_employee = 2

    with pytest.raises(PermissionDeniedError):
        require_customer_update_permission(employee, customer)


def test_customer_update_denies_missing_customer():
    """Deny customer updates when the customer is missing."""
    employee = Mock()
    employee.is_active = True
    employee.role.name = "sales"
    employee.id_employee = 1

    with pytest.raises(PermissionDeniedError):
        require_customer_update_permission(employee, None)


def test_customer_update_denies_unassigned_customer():
    """Deny updates when no sales employee is assigned to the customer."""
    employee = Mock()
    employee.is_active = True
    employee.role.name = "sales"
    employee.id_employee = 1

    customer = Mock()
    customer.id_sales_employee = None

    with pytest.raises(PermissionDeniedError):
        require_customer_update_permission(employee, customer)


@pytest.mark.parametrize("role_name", ["management", "support", "unknown"])
def test_customer_update_denies_unauthorized_roles(role_name):
    """Deny customer updates to roles without the required permission."""
    employee = Mock()
    employee.is_active = True
    employee.role.name = role_name
    employee.id_employee = 1

    customer = Mock()
    customer.id_sales_employee = 1

    with pytest.raises(PermissionDeniedError):
        require_customer_update_permission(employee, customer)


# Test require_contract_update_permission


def test_contract_update_allows_management():
    """Allow management employees to update any contract."""
    employee = Mock()
    employee.is_active = True
    employee.role.name = "management"
    employee.id_employee = 1

    contract = Mock()
    contract.customer.id_sales_employee = 2

    assert require_contract_update_permission(employee, contract) is None


def test_contract_update_allows_assigned_sales_employee():
    """
    Allow sales employees to update contracts
    belonging to their customers.
    """
    employee = Mock()
    employee.is_active = True
    employee.role.name = "sales"
    employee.id_employee = 1

    contract = Mock()
    contract.customer.id_sales_employee = 1

    assert require_contract_update_permission(employee, contract) is None


def test_contract_update_denies_unassigned_sales_employee():
    """Deny sales employees access to contracts of other customers."""
    employee = Mock()
    employee.is_active = True
    employee.role.name = "sales"
    employee.id_employee = 1

    contract = Mock()
    contract.customer.id_sales_employee = 2

    with pytest.raises(PermissionDeniedError):
        require_contract_update_permission(employee, contract)


def test_contract_update_denies_missing_contract():
    """Deny contract updates when the contract is missing."""
    employee = Mock()
    employee.is_active = True
    employee.role.name = "management"

    with pytest.raises(PermissionDeniedError):
        require_contract_update_permission(employee, None)


@pytest.mark.parametrize("role_name", ["management", "sales"])
def test_contract_update_denies_missing_customer(role_name):
    """Deny contract updates when the associated customer is missing."""
    employee = Mock()
    employee.is_active = True
    employee.role.name = role_name

    contract = Mock()
    contract.customer = None

    with pytest.raises(PermissionDeniedError):
        require_contract_update_permission(employee, contract)


@pytest.mark.parametrize("role_name", ["support", "unknown"])
def test_contract_update_denies_unauthorized_roles(role_name):
    """Deny contract updates to roles without the required permission."""
    employee = Mock()
    employee.is_active = True
    employee.role.name = role_name

    contract = Mock()
    contract.customer.id_sales_employee = 1

    with pytest.raises(PermissionDeniedError):
        require_contract_update_permission(employee, contract)


# Test require_event_create_permission


def test_event_create_allows_signed_contract_for_assigned_sales_employee():
    """
    Allow event creation for a signed contract
    belonging to the salesperson.
    """
    employee = Mock()
    employee.is_active = True
    employee.role.name = "sales"
    employee.id_employee = 1

    contract = Mock()
    contract.is_signed = True
    contract.customer.id_sales_employee = 1

    assert require_event_create_permission(employee, contract) is None


def test_event_create_denies_unsigned_contract():
    """Deny event creation when the contract is not signed."""
    employee = Mock()
    employee.is_active = True
    employee.role.name = "sales"
    employee.id_employee = 1

    contract = Mock()
    contract.is_signed = False
    contract.customer.id_sales_employee = 1

    with pytest.raises(PermissionDeniedError):
        require_event_create_permission(employee, contract)


def test_event_create_denies_unassigned_sales_employee():
    """Deny event creation for a contract belonging to another salesperson."""
    employee = Mock()
    employee.is_active = True
    employee.role.name = "sales"
    employee.id_employee = 1

    contract = Mock()
    contract.is_signed = True
    contract.customer.id_sales_employee = 2

    with pytest.raises(PermissionDeniedError):
        require_event_create_permission(employee, contract)


def test_event_create_denies_missing_contract():
    """Deny event creation when the contract is missing."""
    employee = Mock()
    employee.is_active = True
    employee.role.name = "sales"

    with pytest.raises(PermissionDeniedError):
        require_event_create_permission(employee, None)


def test_event_create_denies_missing_customer():
    """Deny event creation when the contract has no associated customer."""
    employee = Mock()
    employee.is_active = True
    employee.role.name = "sales"

    contract = Mock()
    contract.is_signed = True
    contract.customer = None

    with pytest.raises(PermissionDeniedError):
        require_event_create_permission(employee, contract)


@pytest.mark.parametrize("role_name", ["management", "support", "unknown"])
def test_event_create_denies_unauthorized_roles(role_name):
    """Deny event creation to roles without the required permission."""
    employee = Mock()
    employee.is_active = True
    employee.role.name = role_name
    employee.id_employee = 1

    contract = Mock()
    contract.is_signed = True
    contract.customer.id_sales_employee = 1

    with pytest.raises(PermissionDeniedError):
        require_event_create_permission(employee, contract)


# Test require_event_update_permission


def test_event_update_allows_assigned_support_employee():
    """Allow a support employee to update their assigned event."""
    employee = Mock()
    employee.is_active = True
    employee.role.name = "support"
    employee.id_employee = 1

    event = Mock()
    event.id_support_employee = 1

    assert require_event_update_permission(employee, event) is None


def test_event_update_denies_unassigned_support_employee():
    """Deny a support employee access to another employee's event."""
    employee = Mock()
    employee.is_active = True
    employee.role.name = "support"
    employee.id_employee = 1

    event = Mock()
    event.id_support_employee = 2

    with pytest.raises(PermissionDeniedError):
        require_event_update_permission(employee, event)


def test_event_update_denies_event_without_support():
    """Deny event updates when no support employee is assigned."""
    employee = Mock()
    employee.is_active = True
    employee.role.name = "support"
    employee.id_employee = 1

    event = Mock()
    event.id_support_employee = None

    with pytest.raises(PermissionDeniedError):
        require_event_update_permission(employee, event)


def test_event_update_denies_missing_event():
    """Deny event updates when the event is missing."""
    employee = Mock()
    employee.is_active = True
    employee.role.name = "support"

    with pytest.raises(PermissionDeniedError):
        require_event_update_permission(employee, None)


@pytest.mark.parametrize("role_name", ["management", "sales", "unknown"])
def test_event_update_denies_unauthorized_roles(role_name):
    """Deny event updates to roles without the required permission."""
    employee = Mock()
    employee.is_active = True
    employee.role.name = role_name
    employee.id_employee = 1

    event = Mock()
    event.id_support_employee = 1

    with pytest.raises(PermissionDeniedError):
        require_event_update_permission(employee, event)
