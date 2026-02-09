"""Tests for location commands."""

import pytest
from click.testing import CliRunner

from ghl.cli import main


class TestLocationCommands:
    """Test location management commands."""

    def test_locations_list(self, runner, mock_token, mock_location_client, sample_location):
        """Test listing locations."""
        mock_location_client.request.return_value = {"locations": [sample_location]}

        result = runner.invoke(main, ["locations", "list"])
        assert result.exit_code == 0
        assert "Test Location" in result.output
        mock_location_client.request.assert_called_once()

    def test_locations_get(self, runner, mock_token, mock_location_client, sample_location):
        """Test getting a location by ID."""
        mock_location_client.get.return_value = {"location": sample_location}

        result = runner.invoke(main, ["locations", "get", "location-123"])
        assert result.exit_code == 0
        assert "location-123" in result.output
        mock_location_client.get.assert_called_once_with("/locations/location-123")

    def test_locations_switch(self, runner, mock_token, mock_location_id, mock_config_dir):
        """Test switching default location."""
        result = runner.invoke(main, ["locations", "switch", "location-123"])
        assert result.exit_code == 0
        assert "Switched to location" in result.output

    def test_locations_current(self, runner, mock_token, mock_location_id):
        """Test showing current location."""
        result = runner.invoke(main, ["locations", "current"])
        assert result.exit_code == 0
        assert "test-location-id-12345" in result.output
