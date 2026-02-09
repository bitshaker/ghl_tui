"""Contact service - API operations for contacts. Shared by CLI and TUI."""

from __future__ import annotations

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
) -> dict:
    """Update an existing contact. Only provided fields are updated."""
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
    response = client.put(f"/contacts/{contact_id}", json=data)
    return response.get("contact", response)


def delete_contact(client: "GHLClient", contact_id: str) -> None:
    """Delete a contact."""
    client.delete(f"/contacts/{contact_id}")


def search_contacts(client: "GHLClient", query: str, limit: int = 20) -> list[dict]:
    """Search contacts by name, email, or phone."""
    response = client.get("/contacts/", params={"query": query, "limit": limit})
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
