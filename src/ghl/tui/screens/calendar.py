"""Calendar tab: upcoming appointments from GET /calendars/events."""

from __future__ import annotations

from datetime import datetime, timezone
from textual import work
from textual.containers import Container, Vertical
from textual.widgets import DataTable, Label, Static
from textual.worker import Worker, WorkerState

from ...auth import get_location_id, get_token
from ...client import GHLClient
from ...services import calendars as calendars_svc
from ..widgets.rate_limit import HeaderBar


def _format_event_time(raw: str | None) -> str:
    if not raw or not isinstance(raw, str):
        return "—"
    s = raw.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        if "T" in s[:25]:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00")[:32])
        else:
            dt = datetime.fromisoformat(s[:10]).replace(tzinfo=timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone().strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return raw[:19] if len(raw) > 19 else raw


class CalendarView(Container):
    """Calendar events for the location (merged across calendars)."""

    BINDINGS = [
        ("r", "refresh_calendar", "Refresh"),
    ]

    DEFAULT_CSS = """
    CalendarView {
        width: 100%;
        height: auto;
        layout: vertical;
    }
    #calendar-toolbar {
        height: auto;
        padding: 0 0 1 0;
    }
    #calendar-table {
        height: 1fr;
        min-height: 8;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._events: list[dict] = []
        self._calendar_names: dict[str, str] = {}

    def compose(self):
        with Vertical(id="calendar-toolbar"):
            yield Label("Calendar — appointments (next ~30 days by default)", id="calendar-title")
            yield Static("", id="calendar-meta")
        yield DataTable(id="calendar-table", cursor_type="row")

    def on_mount(self) -> None:
        self.load_events()

    @work(thread=True)
    def load_events(self) -> tuple[list[dict], dict[str, str], object]:
        """Fetch events and calendar name map; returns (events, cal_names, rate_limit_info)."""
        location_id = get_location_id()
        with GHLClient(get_token(), location_id) as client:
            cals = client.get("/calendars/").get("calendars", [])
            name_map = {c.get("id", ""): (c.get("name") or c.get("id") or "—") for c in cals}
            events = calendars_svc.list_calendar_events(client, calendars=cals)
            rli = client.rate_limit_info
            return (events, name_map, rli)

    def _refresh_table(self) -> None:
        table = self.query_one("#calendar-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Start", "Title", "Calendar", "Contact ID", "Status")
        for ev in self._events:
            cid = ev.get("calendarId") or ""
            cal_label = self._calendar_names.get(cid, cid[:12] + "…" if len(cid) > 12 else cid or "—")
            title = (ev.get("title") or "").strip() or "—"
            st = _format_event_time(ev.get("startTime"))
            contact = (ev.get("contactId") or "").strip() or "—"
            status = (ev.get("status") or ev.get("appointmentStatus") or "—") or "—"
            table.add_row(st, title, cal_label, contact, status, key=ev.get("id"))

    def action_refresh_calendar(self) -> None:
        self.load_events()

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state != WorkerState.SUCCESS or not event.worker.result:
            return
        result = event.worker.result
        if not isinstance(result, tuple) or len(result) != 3:
            return
        events_list, name_map, rli = result
        try:
            header = self.screen.query_one("#header_bar", HeaderBar)
            header.update_rate_limit(rli)
        except Exception:
            pass
        self._calendar_names = name_map
        self._events = events_list
        self._refresh_table()
        try:
            meta = self.query_one("#calendar-meta", Static)
            meta.update(f"[dim]{len(self._events)} event(s)[/dim]")
        except Exception:
            pass
