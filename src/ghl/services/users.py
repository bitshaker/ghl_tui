"""User service - list users for location (e.g. assigned-to filter)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import GHLClient


def list_users(client: "GHLClient") -> list[dict]:
    """List users in the location. GET /users/ with locationId only (no limit param)."""
    response = client.get("/users/")
    return response.get("users", [])


def user_display_label(user: dict) -> str:
    """Display name for a user row from list_users (matches contact assignee dropdown)."""
    uid = user.get("id") or ""
    label = user.get("name") or user.get("email") or uid or "—"
    return str(label)[:50]


def build_user_id_to_label_map(users: list[dict]) -> dict[str, str]:
    """Map user id -> label for resolving assignedTo on contacts."""
    m: dict[str, str] = {}
    for u in users:
        uid = (u.get("id") or "").strip()
        if uid:
            m[uid] = user_display_label(u)
    return m


def search_users(client: "GHLClient", query: str) -> list[dict]:
    """
    Search users by name or email.
    Uses list_users + client-side filter so it works with location-scoped auth.
    (GET /users/search requires companyId and returns 401 for some auth types.)
    """
    query_lower = (query or "").strip().lower()
    if not query_lower:
        return list_users(client)
    users = list_users(client)
    return [
        u
        for u in users
        if query_lower in (u.get("name") or "").lower()
        or query_lower in (u.get("email") or "").lower()
        or query_lower in (u.get("firstName") or "").lower()
        or query_lower in (u.get("lastName") or "").lower()
    ]
