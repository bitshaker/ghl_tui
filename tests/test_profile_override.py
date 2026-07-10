"""Tests for one-off profile override via --profile and ghl tui PROFILE."""

from unittest.mock import patch

import pytest

from ghl.cli import main
from ghl.config import config_manager


@pytest.fixture
def profiles_setup(runner, mock_config_dir, monkeypatch):
    """Two profiles with work as persisted active; no env var overrides."""
    monkeypatch.delenv("GHL_API_TOKEN", raising=False)
    monkeypatch.delenv("GHL_LOCATION_ID", raising=False)
    runner.invoke(main, ["config", "profiles", "add", "work", "-t", "token-a", "-l", "loc-a"])
    runner.invoke(main, ["config", "profiles", "add", "personal", "-t", "token-b", "-l", "loc-b"])
    runner.invoke(main, ["config", "profiles", "use", "work"])


class TestProfileOverrideCLI:
    """CLI --profile flag and ghl tui PROFILE argument."""

    def test_cli_profile_flag_uses_profile_credentials(
        self, runner, profiles_setup, sample_contacts
    ):
        """--profile uses the named profile's token and location for one command."""
        with patch("ghl.commands.contacts.GHLClient") as mock_cls:
            client_instance = mock_cls.return_value.__enter__.return_value
            client_instance.get.return_value = {"contacts": sample_contacts}

            result = runner.invoke(main, ["--profile", "personal", "contacts", "list"])
            assert result.exit_code == 0
            mock_cls.assert_called_once_with("token-b", "loc-b")

    def test_cli_profile_flag_case_insensitive(
        self, runner, profiles_setup, sample_contacts
    ):
        """--profile resolves profile names case-insensitively."""
        with patch("ghl.commands.contacts.GHLClient") as mock_cls:
            client_instance = mock_cls.return_value.__enter__.return_value
            client_instance.get.return_value = {"contacts": sample_contacts}

            result = runner.invoke(main, ["--profile", "PERSONAL", "contacts", "list"])
            assert result.exit_code == 0
            mock_cls.assert_called_once_with("token-b", "loc-b")

    def test_tui_unknown_profile_fails(self, runner, profiles_setup):
        """ghl tui with unknown profile fails before launching and lists profiles."""
        result = runner.invoke(main, ["tui", "nonexistent"])
        assert result.exit_code != 0
        assert "does not exist" in result.output
        assert "Profiles" in result.output
        assert "work" in result.output
        assert "personal" in result.output

    def test_tui_positional_overrides_global_profile(self, runner, profiles_setup):
        """Positional profile on ghl tui wins over --profile."""
        with patch("ghl.tui.app.run_tui") as run_tui:
            result = runner.invoke(main, ["--profile", "work", "tui", "personal"])
            assert result.exit_code == 0
            run_tui.assert_called_once()
            assert config_manager.get_effective_profile_name() == "personal"
            assert config_manager.get_token() == "token-b"
            assert config_manager.get_location_id() == "loc-b"
