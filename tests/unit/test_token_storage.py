"""Unit tests for local authentication token storage."""

import pytest

from epic_events.security import token_storage


@pytest.fixture
def mock_token_file(monkeypatch, tmp_path):
    """Configure a temporary token storage file for tests."""
    token_file = tmp_path / "token"
    monkeypatch.setattr(token_storage, "TOKEN_FILE", token_file)
    return token_file


# Test "save_token"


def test_save_token_creates_file(mock_token_file):
    """Verify that saving a token creates a new file containing the token."""
    token = "fake.jwt.token"

    token_storage.save_token(token)

    assert mock_token_file.is_file()
    assert mock_token_file.read_text() == token


def test_save_token_overwrites_existing_file(mock_token_file):
    """Verify that saving a new token replaces the previously stored token."""
    token = "fake.jwt.token"

    token_storage.save_token(token)

    assert mock_token_file.is_file()
    assert mock_token_file.read_text() == token

    new_token = "new.fake.jwt.token"

    token_storage.save_token(new_token)

    assert mock_token_file.read_text() == new_token


# Test "load_token"


def test_load_token_existing_file(mock_token_file):
    """Verify that loading an existing token file returns its contents."""
    input_token = "fake.jwt.token"

    mock_token_file.write_text(input_token, encoding="utf-8")

    loaded_token = token_storage.load_token()

    assert loaded_token == input_token


def test_load_token_missing_file(mock_token_file):
    """Verify that loading a nonexistent token file returns None."""
    loaded_token = token_storage.load_token()

    assert loaded_token is None


# Test "delete_token"


def test_delete_token_existing_file(mock_token_file):
    """Verify that deleting a stored token removes its file."""
    token = "fake.jwt.token"
    mock_token_file.write_text(token, encoding="utf-8")

    assert mock_token_file.is_file()
    assert mock_token_file.read_text() == token

    token_storage.delete_token()

    assert not mock_token_file.exists()


def test_delete_token_missing_file(mock_token_file):
    """
    Verify that deleting a nonexistent
    token file does not raise an error.
    """
    token_storage.delete_token()
