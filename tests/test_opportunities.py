"""Tests for opportunity commands."""

import pytest
from click.testing import CliRunner

from ghl.cli import main


class TestOpportunityCommands:
    """Test opportunity management commands."""

    def test_opportunities_list(self, runner, mock_token, mock_location_id, mock_opportunity_client, sample_opportunity):
        """Test listing opportunities."""
        mock_opportunity_client.get.return_value = {"opportunities": [sample_opportunity]}

        result = runner.invoke(main, ["opportunities", "list"])
        assert result.exit_code == 0
        assert "Deal Name" in result.output
        mock_opportunity_client.get.assert_called_once()
        call_args = mock_opportunity_client.get.call_args
        assert "/opportunities/search" in call_args[0][0]

    def test_opportunities_list_with_filters(self, runner, mock_token, mock_location_id, mock_opportunity_client, sample_opportunity):
        """Test listing opportunities with filters."""
        mock_opportunity_client.get.return_value = {"opportunities": [sample_opportunity]}

        result = runner.invoke(
            main,
            [
                "opportunities",
                "list",
                "--pipeline",
                "pipeline-123",
                "--status",
                "open",
                "--limit",
                "10",
            ],
        )
        assert result.exit_code == 0
        mock_opportunity_client.get.assert_called_once()
        call_args = mock_opportunity_client.get.call_args
        params = call_args[1]["params"]
        assert params["pipelineId"] == "pipeline-123"
        assert params["status"] == "open"
        assert params["limit"] == 10

    def test_opportunities_get(self, runner, mock_token, mock_location_id, mock_opportunity_client, sample_opportunity):
        """Test getting an opportunity by ID."""
        mock_opportunity_client.get.return_value = {"opportunity": sample_opportunity}

        result = runner.invoke(main, ["opportunities", "get", "opp-123"])
        assert result.exit_code == 0
        assert "opp-123" in result.output
        mock_opportunity_client.get.assert_called_once_with("/opportunities/opp-123")

    def test_opportunities_create(self, runner, mock_token, mock_location_id, mock_opportunity_client, sample_opportunity):
        """Test creating an opportunity."""
        mock_opportunity_client.post.return_value = {"opportunity": sample_opportunity}

        result = runner.invoke(
            main,
            [
                "opportunities",
                "create",
                "--contact",
                "contact-123",
                "--pipeline",
                "pipeline-123",
                "--stage",
                "stage-123",
                "--name",
                "New Deal",
                "--value",
                "5000",
            ],
        )
        assert result.exit_code == 0
        assert "Opportunity created" in result.output
        mock_opportunity_client.post.assert_called_once()
        call_args = mock_opportunity_client.post.call_args
        assert call_args[0][0] == "/opportunities/"
        data = call_args[1]["json"]
        assert data["contactId"] == "contact-123"
        assert data["pipelineId"] == "pipeline-123"
        assert data["pipelineStageId"] == "stage-123"
        assert data["name"] == "New Deal"
        assert data["monetaryValue"] == 5000.0

    def test_opportunities_create_quiet(self, runner, mock_token, mock_location_id, mock_opportunity_client, sample_opportunity):
        """Test creating an opportunity with --quiet flag."""
        mock_opportunity_client.post.return_value = {"opportunity": sample_opportunity}

        result = runner.invoke(
            main,
            [
                "opportunities",
                "create",
                "--contact",
                "contact-123",
                "--pipeline",
                "pipeline-123",
                "--stage",
                "stage-123",
                "--name",
                "New Deal",
                "--quiet",
            ],
        )
        assert result.exit_code == 0
        # Should only output the opportunity ID
        assert result.output.strip() == "opp-123"
        assert "Opportunity created" not in result.output

    def test_opportunities_move(self, runner, mock_token, mock_location_id, mock_opportunity_client, sample_opportunity):
        """Test moving an opportunity to a new stage."""
        mock_opportunity_client.put.return_value = {"opportunity": sample_opportunity}

        result = runner.invoke(main, ["opportunities", "move", "opp-123", "--stage", "new-stage-123"])
        assert result.exit_code == 0
        assert "Opportunity moved" in result.output
        mock_opportunity_client.put.assert_called_once()
        call_args = mock_opportunity_client.put.call_args
        assert call_args[0][0] == "/opportunities/opp-123"
        assert call_args[1]["json"]["pipelineStageId"] == "new-stage-123"

    def test_opportunities_won(self, runner, mock_token, mock_location_id, mock_opportunity_client, sample_opportunity):
        """Test marking an opportunity as won."""
        sample_opportunity["status"] = "won"
        mock_opportunity_client.put.return_value = {"opportunity": sample_opportunity}

        result = runner.invoke(main, ["opportunities", "won", "opp-123"])
        assert result.exit_code == 0
        assert "Opportunity marked as won" in result.output
        mock_opportunity_client.put.assert_called_once()
        call_args = mock_opportunity_client.put.call_args
        assert call_args[1]["json"]["status"] == "won"

    def test_opportunities_lost(self, runner, mock_token, mock_location_id, mock_opportunity_client, sample_opportunity):
        """Test marking an opportunity as lost."""
        sample_opportunity["status"] = "lost"
        mock_opportunity_client.put.return_value = {"opportunity": sample_opportunity}

        result = runner.invoke(main, ["opportunities", "lost", "opp-123"])
        assert result.exit_code == 0
        assert "Opportunity marked as lost" in result.output
        mock_opportunity_client.put.assert_called_once()
        call_args = mock_opportunity_client.put.call_args
        assert call_args[1]["json"]["status"] == "lost"

    def test_opportunities_delete(self, runner, mock_token, mock_location_id, mock_opportunity_client):
        """Test deleting an opportunity."""
        mock_opportunity_client.delete.return_value = {}

        result = runner.invoke(main, ["opportunities", "delete", "opp-123"], input="y\n")
        assert result.exit_code == 0
        assert "Opportunity deleted" in result.output
        mock_opportunity_client.delete.assert_called_once_with("/opportunities/opp-123")
