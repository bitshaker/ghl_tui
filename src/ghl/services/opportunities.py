"""Opportunity service - API operations for pipeline deals. Shared by CLI and TUI."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..client import GHLClient


def list_opportunities(
    client: "GHLClient",
    *,
    limit: int = 20,
    skip: int = 0,
    pipeline_id: Optional[str] = None,
    stage_id: Optional[str] = None,
    status: Optional[str] = None,
    contact_id: Optional[str] = None,
) -> list[dict]:
    """List opportunities with optional filters. Uses GET /opportunities/search (location only), then filters in Python."""
    params: dict = {}
    if client.location_id:
        params["location_id"] = client.location_id
    response = client.get(
        "/opportunities/search",
        params=params or None,
        include_location_id=False,
        location_param="location_id",
    )
    raw = response.get("opportunities", [])
    if not isinstance(raw, list):
        raw = [raw] if raw else []
    # Filter by contact, pipeline, stage, status (API does not accept these on this endpoint)
    out = []
    for opp in raw:
        if contact_id and opp.get("contactId") != contact_id:
            continue
        if pipeline_id and opp.get("pipelineId") != pipeline_id:
            continue
        if stage_id and opp.get("pipelineStageId") != stage_id:
            continue
        if status and (opp.get("status") or "").lower() != (status or "").lower():
            continue
        out.append(opp)
    return out[skip : skip + limit]


def get_opportunity(client: "GHLClient", opportunity_id: str) -> dict:
    """Get an opportunity by ID."""
    response = client.get(f"/opportunities/{opportunity_id}")
    return response.get("opportunity", response)


def create_opportunity(
    client: "GHLClient",
    *,
    location_id: str,
    contact_id: str,
    pipeline_id: str,
    stage_id: str,
    name: str,
    status: str = "open",
    monetary_value: Optional[float] = None,
    source: Optional[str] = None,
) -> dict:
    """Create a new opportunity."""
    data: dict = {
        "locationId": location_id,
        "contactId": contact_id,
        "pipelineId": pipeline_id,
        "pipelineStageId": stage_id,
        "name": name,
        "status": status,
    }
    if monetary_value is not None:
        data["monetaryValue"] = monetary_value
    if source:
        data["source"] = source
    response = client.post("/opportunities/", json=data)
    return response.get("opportunity", response)


def update_opportunity(
    client: "GHLClient",
    opportunity_id: str,
    *,
    name: Optional[str] = None,
    monetary_value: Optional[float] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
) -> dict:
    """Update an opportunity. Only provided fields are updated."""
    data: dict = {}
    if name is not None:
        data["name"] = name
    if monetary_value is not None:
        data["monetaryValue"] = monetary_value
    if status is not None:
        data["status"] = status
    if source is not None:
        data["source"] = source
    response = client.put(f"/opportunities/{opportunity_id}", json=data)
    return response.get("opportunity", response)


def move_opportunity(client: "GHLClient", opportunity_id: str, stage_id: str) -> dict:
    """Move an opportunity to a different stage."""
    response = client.put(
        f"/opportunities/{opportunity_id}", json={"pipelineStageId": stage_id}
    )
    return response.get("opportunity", response)


def delete_opportunity(client: "GHLClient", opportunity_id: str) -> None:
    """Delete an opportunity."""
    client.delete(f"/opportunities/{opportunity_id}")


def mark_won(client: "GHLClient", opportunity_id: str) -> None:
    """Mark an opportunity as won."""
    client.put(f"/opportunities/{opportunity_id}/status", json={"status": "won"})


def mark_lost(client: "GHLClient", opportunity_id: str) -> None:
    """Mark an opportunity as lost."""
    client.put(f"/opportunities/{opportunity_id}/status", json={"status": "lost"})
