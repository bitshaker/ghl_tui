"""Tests for custom-fields commands."""

import json
import pytest
from click.testing import CliRunner

from ghl.cli import main


class TestCustomFieldsCommands:
    """Test custom-fields list and values commands."""

    def test_custom_fields_list(self, runner, mock_token, mock_location_id, mock_custom_fields_client):
        """Test listing custom fields."""
        mock_custom_fields_client.get.return_value = {
            "customFields": [
                {"id": "cf-1", "name": "Lead Source", "fieldType": "dropdown", "entityType": "contact"},
            ]
        }
        result = runner.invoke(main, ["custom-fields", "list"])
        assert result.exit_code == 0
        assert "Lead Source" in result.output
        assert "cf-1" in result.output
        mock_custom_fields_client.get.assert_called_once()
        call_args = mock_custom_fields_client.get.call_args
        assert f"/locations/{mock_location_id}/customFields" in call_args[0][0]

    def test_custom_fields_list_raw(self, runner, mock_token, mock_location_id, mock_custom_fields_client):
        """Test listing custom fields with --raw dumps API response."""
        raw_response = {"customFields": [{"id": "cf-1", "name": "Lead Source"}]}
        mock_custom_fields_client.get.return_value = raw_response
        result = runner.invoke(main, ["custom-fields", "list", "--raw"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "customFields" in data
        assert len(data["customFields"]) == 1
        assert data["customFields"][0]["name"] == "Lead Source"

    def test_custom_fields_values(self, runner, mock_token, mock_location_id, mock_custom_fields_client):
        """Test listing custom values for a contact."""
        mock_custom_fields_client.get.return_value = {
            "customValues": [
                {"id": "cv-1", "customFieldId": "cf-1", "value": "Website"},
            ]
        }
        result = runner.invoke(main, ["custom-fields", "values", "--contact", "contact-123"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["value"] == "Website"
        mock_custom_fields_client.get.assert_called_once()
        call_args = mock_custom_fields_client.get.call_args
        assert "/customValues" in call_args[0][0]
        assert call_args[1]["params"]["contactId"] == "contact-123"
