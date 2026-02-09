"""Pipeline service - API operations for pipelines and stages. Shared by CLI and TUI."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import GHLClient


def list_pipelines(client: "GHLClient") -> list[dict]:
    """List all pipelines for the location."""
    response = client.get("/opportunities/pipelines")
    return response.get("pipelines", [])


def get_pipeline(client: "GHLClient", pipeline_id: str) -> dict:
    """Get a pipeline by ID (includes stages)."""
    response = client.get(f"/opportunities/pipelines/{pipeline_id}")
    return response.get("pipeline", response)


def list_stages(client: "GHLClient", pipeline_id: str) -> list[dict]:
    """List stages in a pipeline."""
    pipeline = get_pipeline(client, pipeline_id)
    return pipeline.get("stages", [])
