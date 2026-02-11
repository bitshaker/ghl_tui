"""Custom fields service - fetch definitions and manage values for contacts."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..client import GHLClient


def list_custom_fields(client: "GHLClient", location_id: str) -> list[dict]:
    """List custom field definitions for a location (contact-scoped only)."""
    path = f"/locations/{location_id}/customFields"
    response = client.get(path, include_location_id=False)
    fields = response.get("customFields", response.get("fields", []))
    if not isinstance(fields, list):
        return []
    # Filter to contact entity type if field has entityType
    return [f for f in fields if f.get("entityType", "contact") == "contact" or "entityType" not in f]


def list_custom_values(
    client: "GHLClient", location_id: str, contact_id: Optional[str] = None
) -> list[dict]:
    """List custom values for a location, optionally filtered by contact."""
    path = f"/locations/{location_id}/customValues"
    params = {}
    if contact_id:
        params["contactId"] = contact_id
    response = client.get(path, params=params if params else None, include_location_id=False)
    values = response.get("customValues", response.get("values", []))
    if not isinstance(values, list):
        return []
    # Filter by contactId if API returns all values
    if contact_id and values:
        return [v for v in values if v.get("contactId") == contact_id]
    return values


def update_custom_value(
    client: "GHLClient", location_id: str, custom_value_id: str, value: str
) -> dict:
    """Update a custom value by ID."""
    path = f"/locations/{location_id}/customValues/{custom_value_id}"
    response = client.put(path, json={"value": value}, include_location_id=False)
    return response.get("customValue", response)


def create_custom_value(
    client: "GHLClient",
    location_id: str,
    custom_field_id: str,
    contact_id: str,
    value: str,
) -> dict:
    """Create a custom value for a contact."""
    path = f"/locations/{location_id}/customValues"
    data = {
        "customFieldId": custom_field_id,
        "contactId": contact_id,
        "value": value,
    }
    response = client.post(path, json=data, include_location_id=False)
    return response.get("customValue", response)


def extract_custom_values_from_contact(contact: dict) -> dict[str, str]:
    """Extract custom field values from contact object (handles various API shapes)."""
    result: dict[str, str] = {}
    # Try customField (array of {id/customFieldId, value})
    for key in ("customField", "customFieldValues", "customFields"):
        arr = contact.get(key)
        if isinstance(arr, list):
            for item in arr:
                if isinstance(item, dict):
                    fid = item.get("id") or item.get("customFieldId")
                    val = item.get("value") or item.get("values")
                    if fid and val is not None:
                        if isinstance(val, list):
                            result[str(fid)] = val[0] if val else ""
                        else:
                            result[str(fid)] = str(val)
                    elif fid:
                        result[str(fid)] = ""
    # Try customData (object keyed by field id or name)
    if isinstance(contact.get("customData"), dict):
        for k, v in contact["customData"].items():
            if v is not None:
                result[str(k)] = str(v)
    return result


def build_custom_values_map(
    contact: dict,
    custom_values: list[dict],
    field_definitions: list[dict],
) -> dict[str, str]:
    """
    Build field_id -> value map from contact, customValues API, and field definitions.
    Prefers customValues API, then contact-embedded data. Keys are customFieldId.
    """
    result: dict[str, str] = {}
    field_ids = {
        str(f.get("id") or f.get("customFieldId", ""))
        for f in field_definitions
        if f.get("id") or f.get("customFieldId")
    }

    # From customValues API: { customFieldId, value, id } or { customField: { id }, value }
    for cv in custom_values:
        fid = cv.get("customFieldId")
        if not fid and isinstance(cv.get("customField"), dict):
            fid = cv["customField"].get("id")
        if fid:
            fid = str(fid)
            if fid in field_ids:
                val = cv.get("value") or cv.get("values")
                if isinstance(val, list):
                    result[fid] = val[0] if val else ""
                else:
                    result[fid] = str(val) if val is not None else ""

    # From contact object
    from_contact = extract_custom_values_from_contact(contact)
    for fid, val in from_contact.items():
        if fid in field_ids and fid not in result:
            result[fid] = val

    # Ensure all defined fields have an entry
    for f in field_definitions:
        fid = str(f.get("id") or f.get("customFieldId", ""))
        if fid and fid not in result:
            result[fid] = ""

    return result


def save_custom_values(
    client: "GHLClient",
    location_id: str,
    contact_id: str,
    values: dict[str, str],
    value_id_by_field: dict[str, str],
) -> None:
    """Create or update custom values for a contact."""
    for field_id, value in values.items():
        if field_id in value_id_by_field:
            update_custom_value(client, location_id, value_id_by_field[field_id], value)
        else:
            create_custom_value(client, location_id, field_id, contact_id, value)


def build_custom_value_id_map(custom_values: list[dict]) -> dict[str, str]:
    """Map customFieldId -> customValue id for updates."""
    result: dict[str, str] = {}
    for cv in custom_values:
        fid = cv.get("customFieldId")
        if not fid and isinstance(cv.get("customField"), dict):
            fid = cv["customField"].get("id")
        if cv.get("id") and fid:
            result[str(fid)] = str(cv["id"])
    return result
