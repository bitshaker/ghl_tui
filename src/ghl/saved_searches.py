"""Local storage for saved contact search filters."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Optional

from .config import config_manager


def _path(ensure_dir: bool = False) -> Path:
    if ensure_dir:
        config_manager._ensure_config_dir()
    return config_manager.CONFIG_DIR / "saved_searches.json"


def list_saved_searches() -> list[dict[str, Any]]:
    """Load saved searches from disk. Returns list of { id, name, tags, assignedTo, query }."""
    p = _path(ensure_dir=False)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, OSError):
        return []


def save_search(
    *,
    name: str,
    tags: Optional[list[str]] = None,
    assigned_to: Optional[str] = None,
    query: Optional[str] = None,
    id: Optional[str] = None,
) -> dict[str, Any]:
    """Append a saved search and return it. Use id when updating."""
    searches = list_saved_searches()
    if id:
        searches = [s for s in searches if s.get("id") != id]
    record: dict[str, Any] = {
        "id": id or str(uuid.uuid4()),
        "name": name.strip(),
        "tags": list(tags) if tags else [],
        "assignedTo": assigned_to,
        "query": (query or "").strip() or None,
    }
    searches.append(record)
    _path(ensure_dir=True).write_text(json.dumps(searches, indent=2))
    return record


def delete_saved_search(search_id: str) -> bool:
    """Remove a saved search by id. Returns True if found and removed."""
    searches = list_saved_searches()
    before = len(searches)
    searches = [s for s in searches if s.get("id") != search_id]
    if len(searches) == before:
        return False
    _path(ensure_dir=True).write_text(json.dumps(searches, indent=2))
    return True


def get_saved_search(search_id: str) -> Optional[dict[str, Any]]:
    """Get a single saved search by id."""
    for s in list_saved_searches():
        if s.get("id") == search_id:
            return s
    return None
