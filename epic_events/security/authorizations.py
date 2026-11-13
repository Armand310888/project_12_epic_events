"""Define role-based permissions and enforce resource-level access rules."""

from enum import StrEnum, auto

from epic_events.models import Employee


class Permission(StrEnum):
    """Define the permissions available within the Epic Events application."""
    EMPLOYEE_CREATE = auto()
    EMPLOYEE_UPDATE = auto()
    EMPLOYEE_DELETE = auto()

    CUSTOMER_READ = auto()
    CUSTOMER_CREATE = auto()
    CUSTOMER_UPDATE = auto()

    CONTRACT_READ = auto()
    CONTRACT_CREATE = auto()
    CONTRACT_UPDATE = auto()

    EVENT_READ = auto()
    EVENT_CREATE = auto()
    EVENT_UPDATE = auto()
    EVENT_ASSIGN_SUPPORT = auto()


ROLE_PERMISSIONS = {
    "management": {
        Permission.CUSTOMER_READ,
        Permission.CONTRACT_READ,
        Permission.CONTRACT_CREATE,
        Permission.CONTRACT_UPDATE,
        Permission.EVENT_READ,
        Permission.EVENT_ASSIGN_SUPPORT,
        Permission.EMPLOYEE_CREATE,
        Permission.EMPLOYEE_UPDATE,
        Permission.EMPLOYEE_DELETE,
    },
    "sales": {
        Permission.CUSTOMER_READ,
        Permission.CUSTOMER_CREATE,
        Permission.CUSTOMER_UPDATE,
        Permission.CONTRACT_READ,
        Permission.CONTRACT_UPDATE,
        Permission.EVENT_READ,
        Permission.EVENT_CREATE,
    },
    "support": {
        Permission.CUSTOMER_READ,
        Permission.CONTRACT_READ,
        Permission.EVENT_READ,
        Permission.EVENT_UPDATE,
    },
}


def require_general_permission(
    employee: Employee | None,
    permission: Permission,
) -> None:
    """
    Ensure that an active employee's role grants the requested permission.

    Raise PermissionDeniedError if the employee is missing or inactive,
    has no assigned role, has an unknown role,
    or lacks the requested permission.
    """
    if not employee or not employee.is_active:
        raise PermissionDeniedError("Permission denied.")
    if employee.role and (
        employee.role.name in ROLE_PERMISSIONS
        and permission in ROLE_PERMISSIONS[employee.role.name]
    ):
        return

    raise PermissionDeniedError("Permission denied.")


class PermissionDeniedError(Exception):
    """Raised when an employee attempts an unauthorized operation."""
