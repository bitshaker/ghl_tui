"""Workflow service - API operations for workflows. Shared by CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..client import GHLClient


def list_workflows(client: "GHLClient") -> list[dict]:
    """List all workflows for the location."""
    response = client.get("/workflows/")
    return response.get("workflows", [])


def get_workflow(client: "GHLClient", workflow_id: str) -> dict:
    """
    Return workflow metadata by ID.

    GHL only exposes GET /workflows/ (list); there is no GET /workflows/:id.
    """
    for workflow in list_workflows(client):
        if workflow.get("id") == workflow_id:
            return workflow
    raise LookupError(workflow_id)


def add_contact_to_workflow(
    client: "GHLClient",
    contact_id: str,
    workflow_id: str,
    *,
    event_start_time: Optional[str] = None,
) -> dict:
    """Enroll a contact in a workflow (POST /contacts/:id/workflow/:workflowId)."""
    json_body: Optional[dict] = None
    if event_start_time:
        json_body = {"eventStartTime": event_start_time}
    return client.post(
        f"/contacts/{contact_id}/workflow/{workflow_id}",
        json=json_body,
        include_location_id=False,
    )


def remove_contact_from_workflow(
    client: "GHLClient",
    contact_id: str,
    workflow_id: str,
) -> dict:
    """Remove a contact from a workflow (DELETE /contacts/:id/workflow/:workflowId)."""
    return client.delete(
        f"/contacts/{contact_id}/workflow/{workflow_id}",
        include_location_id=False,
    )


def enrollment_succeeded(response: dict) -> bool:
    """True when add/remove workflow API reports success."""
    return bool(
        response.get("succeeded")
        or response.get("succeded")  # GHL typo in some responses
        or response.get("success")
    )
