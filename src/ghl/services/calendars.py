"""Calendar free slots and events (appointments) — shared CLI/TUI helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..client import GHLClient


def ymd_to_utc_start_ms(ymd: str) -> int:
    """Start of UTC day for YYYY-MM-DD as Unix milliseconds."""
    dt = datetime.strptime(ymd, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def ymd_to_utc_end_ms_inclusive(ymd: str) -> int:
    """End of UTC day (inclusive) for YYYY-MM-DD as Unix milliseconds."""
    dt = datetime.strptime(ymd, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end = dt + timedelta(days=1) - timedelta(milliseconds=1)
    return int(end.timestamp() * 1000)


def default_events_time_range_ms(
    start: Optional[str], end: Optional[str]
) -> tuple[int, int]:
    """startTime/endTime for GET /calendars/events (UTC day bounds). Defaults: today → +30 days."""
    today = datetime.now(timezone.utc).date()
    if start:
        d0 = datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        d0 = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    if end:
        d1 = datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end_dt = d1 + timedelta(days=1) - timedelta(milliseconds=1)
    else:
        end_dt = d0 + timedelta(days=30)
    return int(d0.timestamp() * 1000), int(end_dt.timestamp() * 1000)


def events_from_response(response: dict) -> list[dict]:
    """Normalize list payload from GET /calendars/events."""
    for key in ("events", "appointments", "data"):
        val = response.get(key)
        if isinstance(val, list):
            return val
    ev = response.get("event")
    if isinstance(ev, dict):
        return [ev]
    return []


def list_calendar_events(
    client: "GHLClient",
    *,
    calendar_id: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    calendars: Optional[list[dict]] = None,
) -> list[dict]:
    """
    GET /calendars/events requires locationId plus startTime/endTime (ms) and one of
    calendarId, userId, or groupId. When calendar_id is omitted, loads all location
    calendars and merges (deduped by id).
    """
    start_ms, end_ms = default_events_time_range_ms(start, end)
    base = {"startTime": str(start_ms), "endTime": str(end_ms)}

    if calendar_id:
        resp = client.get("/calendars/events", params={**base, "calendarId": calendar_id})
        return events_from_response(resp)

    cals = calendars if calendars is not None else client.get("/calendars/").get("calendars", [])
    seen: set[str] = set()
    merged: list[dict] = []
    for cal in cals:
        cid = cal.get("id")
        if not cid:
            continue
        resp = client.get("/calendars/events", params={**base, "calendarId": cid})
        for ev in events_from_response(resp):
            eid = ev.get("id")
            if eid:
                if eid in seen:
                    continue
                seen.add(eid)
            merged.append(ev)

    merged.sort(key=lambda e: str(e.get("startTime") or ""))
    return merged
