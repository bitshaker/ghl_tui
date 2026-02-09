"""Tests for output format handling."""

import json
import pytest
from click.testing import CliRunner

from ghl.cli import main


class TestOutputFormats:
    """Test different output formats."""

    def test_table_format_default(self, runner, mock_token, mock_location_id, mock_client, sample_contacts, mock_config_dir):
        """Test default table format."""
        # Ensure default format is table
        runner.invoke(main, ["config", "set-format", "table"])
        mock_client.get.return_value = {"contacts": sample_contacts}

        result = runner.invoke(main, ["contacts", "list"])
        assert result.exit_code == 0
        # Table format should include headers and formatted data
        assert "ID" in result.output or "First Name" in result.output
        assert "contact-1" in result.output

    def test_json_format(self, runner, mock_token, mock_location_id, mock_client, sample_contacts):
        """Test JSON output format."""
        mock_client.get.return_value = {"contacts": sample_contacts}

        result = runner.invoke(main, ["contacts", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["id"] == "contact-1"

    def test_csv_format(self, runner, mock_token, mock_location_id, mock_client, sample_contacts):
        """Test CSV output format."""
        mock_client.get.return_value = {"contacts": sample_contacts}

        result = runner.invoke(main, ["contacts", "list", "--csv"])
        assert result.exit_code == 0
        # CSV should have headers
        assert "ID," in result.output
        assert "First Name," in result.output
        # CSV should have data rows
        assert "contact-1" in result.output
        assert "contact-2" in result.output

    def test_quiet_format_list(self, runner, mock_token, mock_location_id, mock_client, sample_contacts):
        """Test quiet format for lists (IDs only)."""
        mock_client.get.return_value = {"contacts": sample_contacts}

        result = runner.invoke(main, ["contacts", "list", "--quiet"])
        assert result.exit_code == 0
        # Should only output IDs, one per line
        output_lines = [line.strip() for line in result.output.strip().split("\n") if line.strip()]
        assert len(output_lines) == 2
        assert "contact-1" in output_lines
        assert "contact-2" in output_lines
        # Should not contain other data
        assert "John" not in result.output
        assert "Doe" not in result.output

    def test_quiet_format_single(self, runner, mock_token, mock_location_id, mock_client, sample_contact):
        """Test quiet format for single items (ID only)."""
        mock_client.post.return_value = {"contact": sample_contact}

        result = runner.invoke(
            main, ["contacts", "create", "--email", "test@example.com", "--quiet"]
        )
        assert result.exit_code == 0
        # Should only output the ID
        assert result.output.strip() == "contact-123"
        assert "Contact created" not in result.output

    def test_config_default_format(self, runner, mock_token, mock_location_id, mock_client, sample_contacts, mock_config_dir):
        """Test using configured default format."""
        # Set default format to JSON
        runner.invoke(main, ["config", "set-format", "json"])

        mock_client.get.return_value = {"contacts": sample_contacts}

        result = runner.invoke(main, ["contacts", "list"])
        assert result.exit_code == 0
        # Should use JSON format from config
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_format_override(self, runner, mock_token, mock_location_id, mock_client, sample_contacts, mock_config_dir):
        """Test that command-line format overrides config."""
        # Set default format to JSON
        runner.invoke(main, ["config", "set-format", "json"])

        mock_client.get.return_value = {"contacts": sample_contacts}

        # Override with CSV
        result = runner.invoke(main, ["contacts", "list", "--csv"])
        assert result.exit_code == 0
        # Should use CSV, not JSON
        assert "ID," in result.output
        assert "First Name," in result.output
