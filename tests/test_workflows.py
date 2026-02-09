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
        mock_workflow_client.get.assert_called_once()

    def test_workflows_get(self, runner, mock_token, mock_location_id, mock_workflow_client, sample_workflow):
        """Test getting a workflow by ID."""
        mock_workflow_client.get.return_value = {"workflow": sample_workflow}

        result = runner.invoke(main, ["workflows", "get", "workflow-123"])
        assert result.exit_code == 0
        assert "workflow-123" in result.output
        mock_workflow_client.get.assert_called_once_with("/workflows/workflow-123")

    def test_workflows_trigger(self, runner, mock_token, mock_location_id, mock_workflow_client):
        """Test triggering a workflow for a contact."""
        mock_workflow_client.post.return_value = {"success": True}

        result = runner.invoke(main, ["workflows", "trigger", "workflow-123", "--contact", "contact-123"])
        assert result.exit_code == 0
        assert "enrolled" in result.output.lower() or "workflow" in result.output.lower()
        mock_workflow_client.post.assert_called_once()
        call_args = mock_workflow_client.post.call_args
        assert "/workflows/workflow-123/enroll" in call_args[0][0]
        assert call_args[1]["json"]["contactId"] == "contact-123"
