"""Tests for pipeline commands."""

import pytest
from click.testing import CliRunner

from ghl.cli import main


class TestPipelineCommands:
    """Test pipeline management commands."""

    def test_pipelines_list(self, runner, mock_token, mock_location_id, mock_pipeline_client, sample_pipeline):
        """Test listing pipelines."""
        mock_pipeline_client.get.return_value = {"pipelines": [sample_pipeline]}

        result = runner.invoke(main, ["pipelines", "list"])
        assert result.exit_code == 0
        assert "Sales Pipeline" in result.output
        mock_pipeline_client.get.assert_called_once()

    def test_pipelines_get(self, runner, mock_token, mock_location_id, mock_pipeline_client, sample_pipeline):
        """Test getting a pipeline by ID."""
        mock_pipeline_client.get.return_value = {"pipeline": sample_pipeline}

        result = runner.invoke(main, ["pipelines", "get", "pipeline-123"])
        assert result.exit_code == 0
        assert "pipeline-123" in result.output
        assert "Lead" in result.output  # Stage name
        mock_pipeline_client.get.assert_called_once_with("/opportunities/pipelines/pipeline-123")

    def test_pipelines_stages(self, runner, mock_token, mock_location_id, mock_pipeline_client, sample_pipeline):
        """Test listing stages in a pipeline."""
        mock_pipeline_client.get.return_value = {"pipeline": sample_pipeline}

        result = runner.invoke(main, ["pipelines", "stages", "pipeline-123"])
        assert result.exit_code == 0
        assert "Lead" in result.output
        assert "Qualified" in result.output
        mock_pipeline_client.get.assert_called_once_with("/opportunities/pipelines/pipeline-123")
