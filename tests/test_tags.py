"""Tests for tag commands."""

import pytest
from click.testing import CliRunner

from ghl.cli import main


class TestTagCommands:
    """Test tag management commands."""

    def test_tags_list(self, runner, mock_token, mock_location_id, mock_tag_client, sample_tag):
        """Test listing tags."""
        mock_tag_client.get.return_value = {"tags": [sample_tag]}

        result = runner.invoke(main, ["tags", "list"])
        assert result.exit_code == 0
        assert "VIP" in result.output
        mock_tag_client.get.assert_called_once()

    def test_tags_get(self, runner, mock_token, mock_location_id, mock_tag_client, sample_tag):
        """Test getting a tag by ID."""
        mock_tag_client.get.return_value = {"tag": sample_tag}

        result = runner.invoke(main, ["tags", "get", "tag-123"])
        assert result.exit_code == 0
        assert "tag-123" in result.output
        mock_tag_client.get.assert_called_once_with("/locations/tags/tag-123")

    def test_tags_create(self, runner, mock_token, mock_location_id, mock_tag_client, sample_tag):
        """Test creating a tag."""
        mock_tag_client.post.return_value = {"tag": sample_tag}

        result = runner.invoke(main, ["tags", "create", "VIP"])
        assert result.exit_code == 0
        assert "Tag created" in result.output
        mock_tag_client.post.assert_called_once()
        call_args = mock_tag_client.post.call_args
        assert call_args[0][0] == "/locations/tags"
        assert call_args[1]["json"]["name"] == "VIP"

    def test_tags_delete(self, runner, mock_token, mock_location_id, mock_tag_client):
        """Test deleting a tag."""
        mock_tag_client.delete.return_value = {}

        result = runner.invoke(main, ["tags", "delete", "tag-123"], input="y\n")
        assert result.exit_code == 0
        assert "Tag deleted" in result.output
        mock_tag_client.delete.assert_called_once_with("/locations/tags/tag-123")
