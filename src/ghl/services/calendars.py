"""Calendar free slots and events (appointments) — shared CLI/TUI helpers."""

from __future__ import annotations

import time as time_mod
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..client import GHLClient

# Short TTL to avoid hammering GET /calendars/ when the TUI refreshes often.
_CALENDAR_LIST_TTL_SEC = 45.0
_calendar_list_cache: dict[str, tuple[float, list[dict]]] = {}


def _iana_timezone_from_calendar_dict(cal: dict) -> str:
    """Best-effort IANA name from GET /calendars/ or GET /calendars/:id payloads."""
    if not isinstance(cal, dict):
        return ""
    for key in ("timezone", "timeZone", "time_zone", "ianaTimezone", "tz"):
        v = cal.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    for nested in ("calendarSettings", "settings", "meta"):
        block = cal.get(nested)
        if isinstance(block, dict):
            for key in ("timezone", "timeZone", "time_zone"):
                v = block.get(key)
                if isinstance(v, str) and v.strip():
                    return v.strip()
    return ""


def _iana_timezone_from_location_payload(loc: dict) -> str:
    """Sub-account timezone from GET /locations/:id."""
    if not isinstance(loc, dict):
        return ""
    for key in ("timezone", "timeZone", "time_zone"):
        v = loc.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def resolve_calendar_timezone(
    client: "GHLClient",
    calendar_id: str,
    calendars: Optional[list[dict]] = None,
) -> str:
    """
    IANA timezone string for booking (selectedTimezone + slot interpretation).

    Uses calendar list/detail (multiple possible field names), then sub-account
    GET /locations/:id when the calendar omits timezone (common cause of UTC
    fallback and wrong wall-clock times).
    """
    cid = (calendar_id or "").strip()
    if not cid:
        return "UTC"
    for c in calendars or []:
        if c.get("id") == cid:
            t = _iana_timezone_from_calendar_dict(c)
            if t:
                return t
            break
    try:
        r = client.get(f"/calendars/{cid}")
        cal = r.get("calendar", r)
        t = _iana_timezone_from_calendar_dict(cal if isinstance(cal, dict) else {})
        if t:
            return t
    except Exception:
        pass
    lid = (getattr(client, "location_id", None) or "").strip()
    if lid:
        try:
            lr = client.get(f"/locations/{lid}")
            loc = lr.get("location", lr)
            t = _iana_timezone_from_location_payload(loc if isinstance(loc, dict) else {})
            if t:
                return t
        except Exception:
            pass
    return "UTC"


def invalidate_location_calendars_cache(location_id: str | None = None) -> None:
    """Drop cached GET /calendars/ for one location or all."""
    if location_id is None:
        _calendar_list_cache.clear()
    else:
        _calendar_list_cache.pop(location_id, None)


def fetch_location_calendars(client: "GHLClient", *, force: bool = False) -> list[dict]:
    """
    GET /calendars/ with per-location TTL caching (reduces duplicate calls from the TUI).
    Pass force=True after invalidate_location_calendars_cache or for a guaranteed refresh.
    """
    lid = (client.location_id or "").strip()
    if not lid:
        return client.get("/calendars/").get("calendars", [])
    now = time_mod.monotonic()
    if not force and lid in _calendar_list_cache:
        ts, cals = _calendar_list_cache[lid]
        if now - ts < _CALENDAR_LIST_TTL_SEC:
            return [dict(c) for c in cals]
    cals = client.get("/calendars/").get("calendars", [])
    _calendar_list_cache[lid] = (now, [dict(c) for c in cals])
    return [dict(c) for c in cals]


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
    """
    startTime/endTime for GET /calendars/events (UTC ms).

    With no filters: last ~48h through +30 days so UTC/local day boundaries do not
    drop “today” appointments for sub-accounts in US timezones.
    """
    now_s = time_mod.time()
    d0: Optional[datetime]
    if start:
        d0 = datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        start_ms = int(d0.timestamp() * 1000)
    else:
        d0 = None
        start_ms = int((now_s - 48 * 3600) * 1000)
    if end:
        d1 = datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end_dt = d1 + timedelta(days=1) - timedelta(milliseconds=1)
        end_ms = int(end_dt.timestamp() * 1000)
    else:
        if d0 is not None:
            end_dt = d0 + timedelta(days=30)
        else:
            end_dt = datetime.fromtimestamp(now_s + 30 * 86400, tz=timezone.utc)
        end_ms = int(end_dt.timestamp() * 1000)
    return start_ms, end_ms


def events_from_response(response: object) -> list[dict]:
    """
    Normalize payload from GET /calendars/events.

    The API normally returns `{ "events": CalendarEventDTO[] }` (see HighLevel SDK
    GetCalendarEventsSuccessfulResponseDTO). Some responses use a top-level JSON
    array, nested `data`, or date-keyed dicts.
    """
    if isinstance(response, list):
        return [x for x in response if isinstance(x, dict)]
    if not isinstance(response, dict):
        return []

    for key in ("events", "appointments", "calendarEvents", "items"):
        val = response.get(key)
        if isinstance(val, list):
            return [x for x in val if isinstance(x, dict)]
        if isinstance(val, dict):
            nested: list[dict] = []
            for inner in val.values():
                if isinstance(inner, list):
                    for item in inner:
                        if isinstance(item, dict):
                            nested.append(item)
                elif isinstance(inner, dict):
                    nested.append(inner)
            if nested:
                return nested

    data = response.get("data")
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        inner = events_from_response(data)
        if inner:
            return inner

    ev = response.get("event")
    if isinstance(ev, dict):
        return [ev]
    return []


def _fetch_events_for_calendar(
    client: "GHLClient",
    base: dict[str, str],
    calendar_id: str,
    calendars: Optional[list[dict]] = None,
) -> list[dict]:
    """
    GET /calendars/events with calendarId, then optional groupId retry (SDK: one of
    calendarId, groupId, userId required).
    """
    cid = (calendar_id or "").strip()
    if not cid:
        return []
    resp = client.get("/calendars/events", params={**base, "calendarId": cid})
    evs = events_from_response(resp)
    if evs:
        return evs

    cal: Optional[dict] = None
    if calendars:
        cal = next((c for c in calendars if c.get("id") == cid), None)
    gid = (cal or {}).get("groupId")
    if isinstance(gid, str) and gid.strip():
        resp_g = client.get("/calendars/events", params={**base, "groupId": gid.strip()})
        evs = events_from_response(resp_g)
        return [e for e in evs if e.get("calendarId") == cid]

    try:
        r = client.get(f"/calendars/{cid}")
        c2 = r.get("calendar", r)
        if isinstance(c2, dict):
            gid2 = c2.get("groupId")
            if isinstance(gid2, str) and gid2.strip():
                resp_g = client.get(
                    "/calendars/events", params={**base, "groupId": gid2.strip()}
                )
                evs = events_from_response(resp_g)
                return [e for e in evs if e.get("calendarId") == cid]
    except Exception:
        pass
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
        return _fetch_events_for_calendar(client, base, calendar_id, calendars)

    cals = calendars if calendars is not None else fetch_location_calendars(client)
    seen: set[str] = set()
    merged: list[dict] = []
    for cal in cals:
        cid = cal.get("id")
        if not cid:
            continue
        for ev in _fetch_events_for_calendar(client, base, str(cid), cals):
            eid = ev.get("id")
            if eid:
                if eid in seen:
                    continue
                seen.add(eid)
            merged.append(ev)

    merged.sort(key=lambda e: str(e.get("startTime") or ""))
    return merged
