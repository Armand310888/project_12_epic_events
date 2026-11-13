"""Define role-based permissions and enforce resource-level access rules."""

from enum import StrEnum, auto

from epic_events.models import Contract, Customer, Employee, Event


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


def require_customer_update_permission(
    employee: Employee | None,
    customer: Customer | None,
) -> None:
    """
    Ensure that a sales employee can update a customer
    they are responsible for.

    Raise PermissionDeniedError if the employee lacks the required permission,
    the customer is missing, or the employee is not assigned to the customer.
    """
    require_general_permission(employee, Permission.CUSTOMER_UPDATE)

    if (
        customer is None
        or customer.id_sales_employee != employee.id_employee
    ):
        raise PermissionDeniedError("Permission denied.")


def require_contract_update_permission(
    employee: Employee | None,
    contract: Contract | None,
) -> None:
    """
    Ensure that an employee is authorized to update a contract.

    Allow management employees to update any contract and sales employees
    to update contracts belonging to their assigned customers.

    Raise PermissionDeniedError if the required permission is missing,
    the contract or its customer is missing, or ownership conditions fail.
    """
    require_general_permission(employee, Permission.CONTRACT_UPDATE)

    if (
        contract is None
        or contract.customer is None
        or (
            employee.role.name == "sales"
            and employee.id_employee != contract.customer.id_sales_employee
        )
    ):
        raise PermissionDeniedError("Permission denied.")


def require_event_create_permission(
    employee: Employee | None,
    contract: Contract | None,
) -> None:
    """
    Ensure that a sales employee can create an event for an eligible contract.

    Require the employee to be responsible for the associated customer
    and the contract to be signed.

    Raise PermissionDeniedError if authorization conditions are not met.
    """
    require_general_permission(employee, Permission.EVENT_CREATE)

    if (
        contract is None
        or contract.customer is None
        or not contract.is_signed
        or contract.customer.id_sales_employee != employee.id_employee
    ):
        raise PermissionDeniedError("Permission denied.")


def require_event_update_permission(
    employee: Employee | None,
    event: Event | None,
) -> None:
    """
    Ensure that a support employee can update an assigned event.

    Require the employee to have the appropriate role and to be assigned
    as the event's support contact.

    Raise PermissionDeniedError if authorization conditions are not met.
    """
    require_general_permission(employee, Permission.EVENT_UPDATE)

    if (
        event is None
        or event.id_support_employee != employee.id_employee
    ):
        raise PermissionDeniedError("Permission denied.")


class PermissionDeniedError(Exception):
    """Raised when an employee attempts an unauthorized operation."""
