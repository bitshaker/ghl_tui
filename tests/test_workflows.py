"""Tests for workflow commands."""

import pytest
from click.testing import CliRunner

from ghl.cli import main


class TestWorkflowCommands:
    """Test workflow management commands."""

    def test_workflows_list(self, runner, mock_token, mock_location_id, mock_workflow_client, sample_workflow):
        """Test listing workflows."""
        mock_workflow_client.get.return_value = {"workflows": [sample_workflow]}

        result = runner.invoke(main, ["workflows", "list"])
        assert result.exit_code == 0
        assert "Welcome Workflow" in result.output
        mock_workflow_client.get.assert_called_once_with("/workflows/")

    def test_workflows_get(self, runner, mock_token, mock_location_id, mock_workflow_client, sample_workflow):
        """Test getting a workflow by ID from the list endpoint."""
        mock_workflow_client.get.return_value = {"workflows": [sample_workflow]}

        result = runner.invoke(main, ["workflows", "get", "workflow-123"])
        assert result.exit_code == 0
        assert "workflow-123" in result.output
        mock_workflow_client.get.assert_called_once_with("/workflows/")

    def test_workflows_get_not_found(self, runner, mock_token, mock_location_id, mock_workflow_client):
        """Test getting a missing workflow."""
        mock_workflow_client.get.return_value = {"workflows": []}

        result = runner.invoke(main, ["workflows", "get", "missing-id"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_workflows_trigger(self, runner, mock_token, mock_location_id, mock_workflow_client):
        """Test enrolling a contact in a workflow."""
        mock_workflow_client.post.return_value = {"succeeded": True}

        result = runner.invoke(main, ["workflows", "trigger", "workflow-123", "--contact", "contact-123"])
        assert result.exit_code == 0
        assert "enrolled" in result.output.lower()
        mock_workflow_client.post.assert_called_once()
        call_args = mock_workflow_client.post.call_args
        assert call_args[0][0] == "/contacts/contact-123/workflow/workflow-123"
        assert call_args[1]["include_location_id"] is False

    def test_contacts_workflow_add(self, runner, mock_token, mock_location_id, mock_client):
        """Test contacts workflow add."""
        mock_client.post.return_value = {"succeeded": True}

        result = runner.invoke(
            main,
            ["contacts", "workflow", "add", "contact-123", "workflow-456"],
        )
        assert result.exit_code == 0
        assert "added" in result.output.lower()
        mock_client.post.assert_called_once()
        assert mock_client.post.call_args[0][0] == "/contacts/contact-123/workflow/workflow-456"

    def test_contacts_workflow_remove(self, runner, mock_token, mock_location_id, mock_client):
        """Test contacts workflow remove."""
        mock_client.delete.return_value = {"succeeded": True}

        result = runner.invoke(
            main,
            ["contacts", "workflow", "remove", "contact-123", "workflow-456"],
        )
        assert result.exit_code == 0
        assert "removed" in result.output.lower()
        mock_client.delete.assert_called_once()
        assert mock_client.delete.call_args[0][0] == "/contacts/contact-123/workflow/workflow-456"
