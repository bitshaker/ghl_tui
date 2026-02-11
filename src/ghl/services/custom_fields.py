"""Custom fields service - fetch definitions and manage values for contacts."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..client import GHLClient


# Field types that have a fixed set of options (dropdown, single-select, radio, etc.)
# GHL uses dataType: "SINGLE_OPTIONS", "MULTI_OPTIONS" (normalized to lowercase)
SELECTION_FIELD_TYPES = frozenset({
    "dropdown", "dropdown_single", "single_option", "single_options",
    "multi_options", "select", "radio", "multiselect", "multiple_options", "multiple_option",
    "single select", "multi select", "single_select", "multi_select",
})


def _field_type(field: dict) -> str:
    """Normalize field type for comparison."""
    t = field.get("fieldType") or field.get("type") or field.get("dataType") or ""
    return str(t).lower().strip()


def _get_options_raw(field: dict) -> list:
    """Get options list from field, trying multiple keys and nested shapes."""
    # GHL uses picklistOptions (list of strings) for dataType SINGLE_OPTIONS / MULTI_OPTIONS
    opts = (
        field.get("picklistOptions")
        or field.get("options")
        or field.get("optionsList")
        or field.get("optionsListObj")
        or field.get("dropdownOptions")
        or field.get("dropdown_options")
    )
    if isinstance(opts, list):
        return opts
    if isinstance(opts, dict):
        return list(opts.items()) if opts else []
    # Nested: data.options, metadata.options, etc.
    for key in ("data", "metadata", "config"):
        nested = field.get(key)
        if isinstance(nested, dict):
            o = nested.get("options") or nested.get("optionsList")
            if isinstance(o, list):
                return o
            if isinstance(o, dict):
                return list(o.items())
    return []


def field_has_options(field: dict) -> bool:
    """Return True if this field has a fixed set of options (dropdown, etc.)."""
    raw = _get_options_raw(field)
    if raw and len(raw) > 0:
        return True
    # Treat as dropdown if field type says so (options might be empty or under different key)
    return _field_type(field) in SELECTION_FIELD_TYPES


def get_field_options(field: dict) -> list[tuple[str, str]]:
    """
    Extract (display_label, value) options for dropdown/select fields.
    Handles common API shapes: {value, name}, {id, name}, {label, value}, (key, val) tuples, etc.
    """
    raw = _get_options_raw(field)
    result: list[tuple[str, str]] = []
    for item in raw:
        if isinstance(item, str):
            result.append((item, item))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            result.append((str(item[0]), str(item[1])))
        elif isinstance(item, dict):
            # GHL often uses optionKey/optionValue, or option (display) with value
            label = (
                item.get("name") or item.get("label") or item.get("value") or item.get("id")
                or item.get("text") or item.get("option") or item.get("optionValue") or item.get("optionKey") or ""
            )
            val = (
                item.get("value") or item.get("id") or item.get("name") or item.get("key")
                or item.get("optionKey") or item.get("optionValue") or item.get("option") or label
            )
            if label or val:
                result.append((str(label), str(val)))
    if result:
        return result
    # Fallback: string list under other keys (values, choices, enum, etc.)
    for key in ("values", "choices", "enum", "items"):
        arr = field.get(key)
        if isinstance(arr, list) and arr:
            for v in arr:
                if isinstance(v, str):
                    result.append((v, v))
                elif isinstance(v, dict):
                    label = v.get("name") or v.get("label") or v.get("value") or ""
                    val = v.get("value") or v.get("id") or label
                    if label or val:
                        result.append((str(label), str(val)))
            if result:
                return result
    return result


# Custom fields to hide from TUI/editing (e.g. "Notes" is separate from contact notes feature)
HIDDEN_CUSTOM_FIELD_KEYS = frozenset({"contact.notes"})
HIDDEN_CUSTOM_FIELD_NAMES = frozenset({"notes"})


def _is_hidden_custom_field(field: dict) -> bool:
    """Return True if this field should not be shown or edited (e.g. Notes)."""
    key = (field.get("fieldKey") or field.get("key") or "").strip().lower()
    name = (field.get("name") or field.get("label") or "").strip().lower()
    if key and key in HIDDEN_CUSTOM_FIELD_KEYS:
        return True
    if name and name in HIDDEN_CUSTOM_FIELD_NAMES:
        return True
    return False


def list_custom_fields(client: "GHLClient", location_id: str) -> list[dict]:
    """List custom field definitions for a location (contact-scoped only)."""
    path = f"/locations/{location_id}/customFields"
    response = client.get(path, include_location_id=False)
    fields = response.get("customFields", response.get("fields", []))
    if not isinstance(fields, list):
        return []
    # Filter to contact entity type (entityType or model)
    contact_fields = [
        f for f in fields
        if f.get("entityType", f.get("model", "contact")) == "contact" or "entityType" not in f
    ]
    # Exclude hidden fields (e.g. Notes custom field; we use contact notes instead)
    return [f for f in contact_fields if not _is_hidden_custom_field(f)]


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
