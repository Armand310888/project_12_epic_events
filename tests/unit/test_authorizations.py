"""Unit tests for role-based permissions and access control."""

from unittest.mock import Mock

import pytest

from epic_events.security.authorizations import (
    Permission,
    PermissionDeniedError,
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
