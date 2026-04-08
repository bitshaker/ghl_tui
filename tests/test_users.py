"""Tests for user commands."""

import pytest
from click.testing import CliRunner

from ghl.cli import main
from ghl.services import users as users_svc


class TestUserCommands:
    """Test user management commands."""

    def test_users_list(self, runner, mock_token, mock_location_id, mock_user_client, sample_user):
        """Test listing users."""
        mock_user_client.get.return_value = {"users": [sample_user]}

        result = runner.invoke(main, ["users", "list"])
        assert result.exit_code == 0
        assert "Admin" in result.output
        mock_user_client.get.assert_called_once()

    def test_users_get(self, runner, mock_token, mock_location_id, mock_user_client, sample_user):
        """Test getting a user by ID."""
        mock_user_client.get.return_value = {"user": sample_user}

        result = runner.invoke(main, ["users", "get", "user-123"])
        assert result.exit_code == 0
        assert "user-123" in result.output
        mock_user_client.get.assert_called_once_with("/users/user-123")

    def test_users_me(self, runner, mock_token, mock_user_client, sample_user):
        """Test getting current user."""
        mock_user_client.get.return_value = {"user": sample_user}

        result = runner.invoke(main, ["users", "me"])
        assert result.exit_code == 0
        assert "admin@example.com" in result.output
        mock_user_client.get.assert_called_once_with("/users/me")

    def test_users_search(self, runner, mock_token, mock_location_id, mock_user_client, sample_user):
        """Test searching users (uses list + client-side filter; no query param sent to API)."""
        mock_user_client.get.return_value = {"users": [sample_user]}

        result = runner.invoke(main, ["users", "search", "admin"])
        assert result.exit_code == 0
        assert "Admin" in result.output
        mock_user_client.get.assert_called_once()
        call_args = mock_user_client.get.call_args
        assert call_args[0][0] == "/users/"


class TestUserDisplayHelpers:
    def test_user_display_label_prefers_name(self) -> None:
        assert users_svc.user_display_label(
            {"id": "u1", "name": "Jane Doe", "email": "j@x.com"}
        ) == "Jane Doe"

    def test_user_display_label_falls_back_to_email(self) -> None:
        assert users_svc.user_display_label({"id": "u1", "email": "j@x.com"}) == "j@x.com"

    def test_build_user_id_to_label_map(self) -> None:
        users = [
            {"id": "a", "name": "Alice"},
            {"id": "b", "email": "bob@x.com"},
        ]
        m = users_svc.build_user_id_to_label_map(users)
        assert m == {"a": "Alice", "b": "bob@x.com"}
