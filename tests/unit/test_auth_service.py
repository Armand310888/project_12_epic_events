"""Unit tests for employee authentication."""

import pytest

from epic_events.services import auth_service

# Test 'logout_employee'


def test_logout_employee_with_existing_token(monkeypatch):
    """Delete the stored token and return True when one exists."""
    deleted = []

    monkeypatch.setattr(
        auth_service,
        "load_token",
        lambda: "valid-token",
    )
    monkeypatch.setattr(
        auth_service,
        "delete_token",
        lambda: deleted.append(True),
    )

    result = auth_service.logout_employee()

    assert result is True
    assert deleted == [True]


def test_logout_employee_without_token(monkeypatch):
    """Return False without deleting anything when no token exists."""
    deleted = []

    monkeypatch.setattr(
        auth_service,
        "load_token",
        lambda: None,
    )
    monkeypatch.setattr(
        auth_service,
        "delete_token",
        lambda: deleted.append(True),
    )

    result = auth_service.logout_employee()

    assert result is False
    assert deleted == []


def test_logout_employee_when_deletion_fails(monkeypatch):
    """Propagate an error when the stored token cannot be deleted."""
    def failing_delete():
        raise PermissionError("Cannot delete token.")

    monkeypatch.setattr(
        auth_service,
        "load_token",
        lambda: "valid-token",
    )
    monkeypatch.setattr(
        auth_service,
        "delete_token",
        failing_delete,
    )

    with pytest.raises(PermissionError, match="Cannot delete token."):
        auth_service.logout_employee()
