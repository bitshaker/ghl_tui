"""Location-level task search (POST /locations/:locationId/tasks/search)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ..client import GHLClient


def search_tasks(
    client: "GHLClient",
    location_id: str,
    *,
    assignee_id: Optional[str] = None,
    status: Optional[str] = None,
    query: Optional[str] = None,
    contact_ids: Optional[list[str]] = None,
    limit: Optional[int] = None,
    skip: Optional[int] = None,
    body_extra: Optional[dict[str, Any]] = None,
) -> list[dict]:
    """Search tasks at location level. Body is required.

    Request body format: contactId (array), completed (bool), assignedTo (array),
    query, limit, skip, businessId.

    Args:
        client: GHL client.
        location_id: Location (sub-account) ID.
        assignee_id: Optional user ID to filter by assignee (sent as assignedTo array).
        status: Optional "pending", "completed", or None for all (sent as completed: false/true).
        query: Optional text search.
        contact_ids: Optional list of contact IDs to filter by.
        limit: Optional max results.
        skip: Optional pagination offset.
        body_extra: Optional extra keys to merge into the request body.

    Returns:
        List of task dicts (e.g. id, title, body, dueDate, completed, contactId).
    """
    path = f"/locations/{location_id}/tasks/search"
    body: dict[str, Any] = {}
    if assignee_id:
        body["assignedTo"] = [assignee_id]
    if status == "pending":
        body["completed"] = False
    elif status == "completed":
        body["completed"] = True
    if query:
        body["query"] = query.strip()
    if contact_ids:
        body["contactId"] = contact_ids
    if limit is not None:
        body["limit"] = limit
    if skip is not None:
        body["skip"] = skip
    if body_extra:
        body.update(body_extra)
    response = client.post(path, json=body, include_location_id=False)
    raw = (
        response.get("tasks", response.get("task", []))
        if isinstance(response, dict)
        else response
    )
    if not isinstance(raw, list):
        return []
    # Normalize: API returns _id, contactDetails, assignedToUserDetails
    out = []
    for t in raw:
        if not isinstance(t, dict):
            continue
        task = dict(t)
        if "_id" in task and "id" not in task:
            task["id"] = task["_id"]
        cd = task.get("contactDetails") or {}
        if isinstance(cd, dict):
            name = (
                (cd.get("firstName") or "").strip()
                + " "
                + (cd.get("lastName") or "").strip()
            ).strip()
            if name:
                task["contactName"] = name
        ad = task.get("assignedToUserDetails") or {}
        if isinstance(ad, dict) and (ad.get("firstName") or ad.get("lastName")):
            task["assigneeName"] = (
                (ad.get("firstName") or "").strip()
                + " "
                + (ad.get("lastName") or "").strip()
            ).strip() or ad.get("id") or ""
        out.append(task)
    return out
