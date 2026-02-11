"""Contact service - API operations for contacts. Shared by CLI and TUI."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..client import GHLClient


def list_contacts(client: "GHLClient", limit: int = 20, query: Optional[str] = None) -> list[dict]:
    """List contacts in the location."""
    params: dict = {"limit": limit}
    if query:
        params["query"] = query
    response = client.get("/contacts/", params=params)
    return response.get("contacts", [])


def get_contact(client: "GHLClient", contact_id: str) -> dict:
    """Get a contact by ID."""
    response = client.get(f"/contacts/{contact_id}")
    return response.get("contact", response)


def create_contact(
    client: "GHLClient",
    *,
    location_id: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    name: Optional[str] = None,
    company_name: Optional[str] = None,
    source: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> dict:
    """Create a new contact. Requires at least email or phone."""
    data: dict = {"locationId": location_id}
    if email:
        data["email"] = email
    if phone:
        data["phone"] = phone
    if first_name:
        data["firstName"] = first_name
    if last_name:
        data["lastName"] = last_name
    if name:
        data["name"] = name
    if company_name:
        data["companyName"] = company_name
    if source:
        data["source"] = source
    if tags:
        data["tags"] = tags
    response = client.post("/contacts/", json=data)
    return response.get("contact", response)


def update_contact(
    client: "GHLClient",
    contact_id: str,
    *,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    company_name: Optional[str] = None,
    source: Optional[str] = None,
    custom_fields: Optional[list[dict]] = None,
) -> dict:
    """Update an existing contact. Only provided fields are updated.

    custom_fields: optional list of { id, key, field_value } for custom field
    values (sent in Update Contact body; no separate custom-values scope needed).
    """
    data: dict = {}
    if email is not None:
        data["email"] = email
    if phone is not None:
        data["phone"] = phone
    if first_name is not None:
        data["firstName"] = first_name
    if last_name is not None:
        data["lastName"] = last_name
    if company_name is not None:
        data["companyName"] = company_name
    if source is not None:
        data["source"] = source
    if custom_fields is not None and len(custom_fields) > 0:
        data["customFields"] = custom_fields
    response = client.put(f"/contacts/{contact_id}", json=data)
    return response.get("contact", response)


def delete_contact(client: "GHLClient", contact_id: str) -> None:
    """Delete a contact."""
    client.delete(f"/contacts/{contact_id}")


def search_contacts(client: "GHLClient", query: str, limit: int = 20) -> list[dict]:
    """Search contacts by name, email, or phone."""
    response = client.get("/contacts/", params={"query": query, "limit": limit})
    return response.get("contacts", [])


def contacts_search(
    client: "GHLClient",
    location_id: str,
    *,
    page: int = 1,
    page_limit: int = 50,
    query: Optional[str] = None,
    tags: Optional[list[str]] = None,
    assigned_to: Optional[str] = None,
) -> list[dict]:
    """
    Search contacts via POST /contacts/search with filters.
    Supports filter by tags (contains, AND across multiple) and assignedTo (eq).
    """
    filters: list[dict] = []
    if assigned_to:
        filters.append({"field": "assignedTo", "operator": "eq", "value": assigned_to})
    if tags:
        for tag in tags:
            tag = (tag or "").strip()
            if tag:
                filters.append({"field": "tags", "operator": "contains", "value": tag})

    body: dict = {
        "locationId": location_id,
        "page": page,
        "pageLimit": page_limit,
    }
    if query:
        body["query"] = query.strip()
    if filters:
        body["filters"] = [{"group": "AND", "filters": filters}]

    response = client.post(
        "/contacts/search",
        json=body,
        include_location_id=False,
    )
    return response.get("contacts", [])


def add_tag(client: "GHLClient", contact_id: str, tags: list[str]) -> None:
    """Add tags to a contact (merges with existing)."""
    contact = get_contact(client, contact_id)
    existing = contact.get("tags", []) or []
    all_tags = list(set(existing + tags))
    client.put(f"/contacts/{contact_id}", json={"tags": all_tags})


def remove_tag(client: "GHLClient", contact_id: str, tags: list[str]) -> None:
    """Remove tags from a contact."""
    contact = get_contact(client, contact_id)
    existing = contact.get("tags", []) or []
    new_tags = [t for t in existing if t not in tags]
    client.put(f"/contacts/{contact_id}", json={"tags": new_tags})


def list_notes(client: "GHLClient", contact_id: str) -> list[dict]:
    """List notes for a contact."""
    response = client.get(
        f"/contacts/{contact_id}/notes", include_location_id=False
    )
    return response.get("notes", [])


def add_note(client: "GHLClient", contact_id: str, body: str) -> dict:
    """Add a note to a contact."""
    response = client.post(
        f"/contacts/{contact_id}/notes",
        json={"body": body},
        include_location_id=False,
    )
    return response.get("note", response)


def list_tasks(client: "GHLClient", contact_id: str) -> list[dict]:
    """List tasks for a contact."""
    response = client.get(
        f"/contacts/{contact_id}/tasks", include_location_id=False
    )
    return response.get("tasks", [])


def create_task(
    client: "GHLClient",
    contact_id: str,
    title: str,
    *,
    body: Optional[str] = None,
    due_date: Optional[str] = None,
    completed: bool = False,
    assigned_to: Optional[str] = None,
) -> dict:
    """Create a task for a contact.
    GHL API requires title, dueDate (ISO 8601), and completed.
    """
    # dueDate is required; default to 7 days from now at noon UTC
    if due_date:
        due_date_str = due_date
    else:
        default_due = datetime.now(timezone.utc) + timedelta(days=7)
        due_date_str = default_due.strftime("%Y-%m-%dT12:00:00Z")
    data: dict = {
        "title": title,
        "dueDate": due_date_str,
        "completed": completed,
    }
    if body is not None:
        data["body"] = body
    if assigned_to is not None:
        data["assignedTo"] = assigned_to
    response = client.post(
        f"/contacts/{contact_id}/tasks",
        json=data,
        include_location_id=False,
    )
    return response.get("task", response)


def update_task(
    client: "GHLClient",
    contact_id: str,
    task_id: str,
    *,
    title: Optional[str] = None,
    due_date: Optional[str] = None,
) -> dict:
    """Update a task."""
    data: dict = {}
    if title is not None:
        data["title"] = title
    if due_date is not None:
        data["dueDate"] = due_date
    if not data:
        return get_task(client, contact_id, task_id)
    response = client.put(
        f"/contacts/{contact_id}/tasks/{task_id}",
        json=data,
        include_location_id=False,
    )
    return response.get("task", response)


def get_task(client: "GHLClient", contact_id: str, task_id: str) -> dict:
    """Get a single task by ID."""
    response = client.get(
        f"/contacts/{contact_id}/tasks/{task_id}",
        include_location_id=False,
    )
    return response.get("task", response)


def delete_task(client: "GHLClient", contact_id: str, task_id: str) -> None:
    """Delete a task."""
    client.delete(
        f"/contacts/{contact_id}/tasks/{task_id}",
        include_location_id=False,
    )


def update_task_completed(
    client: "GHLClient", contact_id: str, task_id: str, completed: bool
) -> dict:
    """Mark a task as completed or incomplete."""
    response = client.put(
        f"/contacts/{contact_id}/tasks/{task_id}/completed",
        json={"completed": completed},
        include_location_id=False,
    )
    return response.get("task", response)
