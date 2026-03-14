"""Tests for tasks commands."""

import pytest
from click.testing import CliRunner

from ghl.cli import main


class TestTasksCommands:
    """Test tasks search command."""

    def test_tasks_search(self, runner, mock_token, mock_location_id, mock_tasks_client):
        """Test searching tasks."""
        mock_tasks_client.post.return_value = {
            "tasks": [
                {
                    "id": "task-1",
                    "title": "Follow up",
                    "body": "Call back",
                    "dueDate": "2024-01-15",
                    "completed": False,
                    "contactName": "John Doe",
                    "assigneeName": "Agent Smith",
                }
            ],
            "total": 1,
        }
        result = runner.invoke(main, ["tasks", "search"])
        assert result.exit_code == 0
        assert "Follow up" in result.output
        assert "task-1" in result.output
        mock_tasks_client.post.assert_called_once()
        call_args = mock_tasks_client.post.call_args
        assert f"/locations/{mock_location_id}/tasks/search" in call_args[0][0]
        assert call_args[1]["json"] == {}

    def test_tasks_search_with_filters(self, runner, mock_token, mock_location_id, mock_tasks_client):
        """Test searching tasks with assignee, status, query, limit."""
        mock_tasks_client.post.return_value = {"tasks": [], "total": 0}
        result = runner.invoke(
            main,
            [
                "tasks",
                "search",
                "--assignee", "user-456",
                "--status", "pending",
                "--query", "call",
                "--limit", "10",
                "--skip", "0",
            ],
        )
        assert result.exit_code == 0
        mock_tasks_client.post.assert_called_once()
        body = mock_tasks_client.post.call_args[1]["json"]
        assert body["assignedTo"] == ["user-456"]
        assert body["completed"] is False
        assert body["query"] == "call"
        assert body["limit"] == 10
        assert body["skip"] == 0
