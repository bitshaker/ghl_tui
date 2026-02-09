"""Tests for user commands."""

import pytest
from click.testing import CliRunner

from ghl.cli import main


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
        """Test searching users."""
        mock_user_client.get.return_value = {"users": [sample_user]}

        result = runner.invoke(main, ["users", "search", "admin"])
        assert result.exit_code == 0
        assert "Admin" in result.output
        mock_user_client.get.assert_called_once()
        call_args = mock_user_client.get.call_args
        assert call_args[1]["params"]["query"] == "admin"
