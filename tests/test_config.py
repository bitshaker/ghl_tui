"""Tests for configuration commands."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from ghl.cli import main


class TestConfigCommands:
    """Test configuration management commands."""

    def test_config_show_no_config(self, runner, mock_config_dir):
        """Test showing config when nothing is configured."""
        result = runner.invoke(main, ["config", "show"])
        assert result.exit_code == 0
        assert "Not set" in result.output

    def test_config_set_location(self, runner, mock_config_dir, mock_token):
        """Test setting location ID."""
        result = runner.invoke(main, ["config", "set-location", "test-location-123"])
        assert result.exit_code == 0
        assert "Default location set to: test-location-123" in result.output

        # Verify it's saved
        config_file = mock_config_dir / "config.json"
        assert config_file.exists()
        config_data = json.loads(config_file.read_text())
        assert config_data["location_id"] == "test-location-123"

    def test_config_set_format(self, runner, mock_config_dir, mock_token):
        """Test setting output format."""
        for format_type in ["table", "json", "csv"]:
            result = runner.invoke(main, ["config", "set-format", format_type])
            assert result.exit_code == 0
            assert f"Default output format set to: {format_type}" in result.output

            # Verify it's saved
            config_file = mock_config_dir / "config.json"
            assert config_file.exists()
            config_data = json.loads(config_file.read_text())
            assert config_data["output_format"] == format_type

    def test_config_set_format_invalid(self, runner, mock_config_dir):
        """Test setting invalid output format."""
        result = runner.invoke(main, ["config", "set-format", "invalid"])
        assert result.exit_code != 0

    def test_config_show_with_config(self, runner, mock_config_dir, mock_token):
        """Test showing config with values set."""
        # Set location and format
        runner.invoke(main, ["config", "set-location", "test-location-123"])
        runner.invoke(main, ["config", "set-format", "json"])

        result = runner.invoke(main, ["config", "show"])
        assert result.exit_code == 0
        assert "test-location-123" in result.output
        assert "json" in result.output
        assert "Configured" in result.output or "Not set" in result.output

    def test_config_clear_token(self, runner, mock_config_dir, mock_token):
        """Test clearing token."""
        # First set a token via credentials file
        creds_file = mock_config_dir / "credentials.json"
        creds_file.write_text(json.dumps({"api_token": "test-token"}))
        creds_file.chmod(0o600)

        result = runner.invoke(main, ["config", "clear", "--token"], input="y\n")
        assert result.exit_code == 0
        assert "API token cleared" in result.output
        assert not creds_file.exists()

    def test_config_clear_all(self, runner, mock_config_dir, mock_token):
        """Test clearing all configuration."""
        # Set up some config
        runner.invoke(main, ["config", "set-location", "test-location-123"])
        creds_file = mock_config_dir / "credentials.json"
        creds_file.write_text(json.dumps({"api_token": "test-token"}))
        creds_file.chmod(0o600)

        result = runner.invoke(main, ["config", "clear", "--all"], input="y\n")
        assert result.exit_code == 0
        assert "All configuration cleared" in result.output
        assert not creds_file.exists()

    def test_config_set_token_interactive(self, runner, mock_config_dir):
        """Test setting token interactively."""
        result = runner.invoke(main, ["config", "set-token"], input="test-token-123\n")
        assert result.exit_code == 0
        assert "API token saved successfully" in result.output

        # Verify it's saved
        creds_file = mock_config_dir / "credentials.json"
        assert creds_file.exists()
        creds_data = json.loads(creds_file.read_text())
        assert creds_data["api_token"] == "test-token-123"

    def test_config_set_token_argument(self, runner, mock_config_dir):
        """Test setting token as argument."""
        result = runner.invoke(main, ["config", "set-token", "test-token-456"])
        assert result.exit_code == 0
        assert "API token saved successfully" in result.output

        # Verify it's saved
        creds_file = mock_config_dir / "credentials.json"
        assert creds_file.exists()
        creds_data = json.loads(creds_file.read_text())
        assert creds_data["api_token"] == "test-token-456"
