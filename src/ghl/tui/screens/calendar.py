"""Calendar tab: appointments with calendar filter and CRUD."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

import httpx
from rich.text import Text
from textual import on, work
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Label, Select, Static
from textual.worker import Worker, WorkerState

from ...auth import get_location_id, get_token
from ...client import APIError, GHLClient
from ...services import calendars as calendars_svc
from ..calendar_appointments import (
    CreateAppointmentModal,
    DeleteAppointmentModal,
    EditAppointmentModal,
)
from ..transport_errors import notify_transport_error, transport_error_toast_message
from ..widgets.rate_limit import HeaderBar


def _parse_api_datetime_string(s: str) -> Optional[datetime]:
    """
    Parse GHL calendar event datetimes (e.g. 2026-03-25T10:00:00-07:00).

    Python < 3.11 fromisoformat is picky about some offset forms; normalize
    ...±HH:MM to ...±HHMM when needed.
    """
    s = s.strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    candidates = [s]
    if re.search(r"[+-]\d{2}:\d{2}$", s):
        candidates.append(re.sub(r"([+-]\d{2}):(\d{2})$", r"\1\2", s))
    for cand in candidates:
        try:
            dt = datetime.fromisoformat(cand)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        try:
            return datetime.fromisoformat(s[:10]).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def _format_event_time(raw: object | None) -> str:
    """Format API startTime (ISO string or Unix ms per CalendarEventDTO)."""
    if raw is None:
        return "—"
    if isinstance(raw, (int, float)):
        try:
            dt = datetime.fromtimestamp(float(raw) / 1000.0, tz=timezone.utc)
            return dt.astimezone().strftime("%Y-%m-%d %H:%M")
        except (OSError, OverflowError, ValueError):
            return "—"
    if isinstance(raw, str):
        s2 = raw.strip()
        if s2.isdigit() and len(s2) >= 12:
            try:
                dt = datetime.fromtimestamp(int(s2) / 1000.0, tz=timezone.utc)
                return dt.astimezone().strftime("%Y-%m-%d %H:%M")
            except (OSError, OverflowError, ValueError):
                pass
    if not isinstance(raw, str):
        return str(raw)[:32]
    dt = _parse_api_datetime_string(raw)
    if dt is not None:
        return dt.astimezone().strftime("%Y-%m-%d %H:%M")
    s = raw.strip()
    return s[:19] if len(s) > 19 else s


def _cell(value: object) -> Text:
    """Plain Rich Text cell (DataTable parses str as markup; Text is not re-parsed)."""
    s = str(value) if value is not None else "—"
    return Text(s, no_wrap=True, end="")


class CalendarView(Container):
    """Calendar events with filter, refresh, and appointment CRUD."""

    BINDINGS = [
        ("r", "refresh_calendar", "Refresh"),
        ("n", "new_appointment", "New"),
        ("e", "edit_appointment", "Edit"),
        ("d", "delete_appointment", "Delete"),
    ]

    DEFAULT_CSS = """
    CalendarView {
        width: 100%;
        height: 1fr;
        layout: vertical;
    }
    #calendar-toolbar {
        height: auto;
        padding: 0 0 1 0;
    }
    #calendar-filters {
        height: auto;
        padding: 0 0 1 0;
    }
    #calendar-actions {
        height: auto;
        padding: 0 0 1 0;
    }
    #calendar-actions Button {
        margin-right: 1;
    }
    #calendar-meta {
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
        self._calendars_list: list[dict] = []
        self._calendar_filter_id: Optional[str] = None
        self._suppress_calendar_select = False

    def _clear_calendar_select_suppress(self) -> None:
        """Allow Select.Changed after programmatic set_options (see _update_calendar_select)."""
        self._suppress_calendar_select = False

    def compose(self):
        """Mirror TasksView: title toolbar, filter row, action row, meta line, DataTable last."""
        with Vertical(id="calendar-toolbar"):
            yield Label(
                "Calendar — appointments (next ~30 days); filter by calendar or All",
                id="calendar-title",
            )
        with Horizontal(id="calendar-filters"):
            yield Label("Calendar:")
            yield Select(
                [("All calendars", "")],
                value="",
                allow_blank=True,
                id="calendar-select",
            )
        with Horizontal(id="calendar-actions"):
            yield Button("New", variant="primary", id="btn-cal-new")
            yield Button("Edit", id="btn-cal-edit")
            yield Button("Delete", variant="error", id="btn-cal-delete")
        yield Static("", id="calendar-meta")
        yield DataTable(id="calendar-table", cursor_type="row")

    def on_mount(self) -> None:
        self.load_events()

    @on(Select.Changed, "#calendar-select")
    def on_calendar_filter_changed(self, event: Select.Changed) -> None:
        if self._suppress_calendar_select:
            return
        raw = event.value
        val = (raw or "").strip() if isinstance(raw, str) else ""
        new_filter: Optional[str] = val if val else None
        if new_filter == self._calendar_filter_id:
            return
        self._calendar_filter_id = new_filter
        self.load_events()

    @work(thread=True, exclusive=True)
    def load_events(self) -> tuple[list[dict], dict[str, str], list[dict], object]:
        """Fetch events, name map, calendars list, rate limit info."""
        location_id = get_location_id()
        try:
            with GHLClient(get_token(), location_id) as client:
                cals = calendars_svc.fetch_location_calendars(client)
                name_map = {c.get("id", ""): (c.get("name") or c.get("id") or "—") for c in cals}
                events = calendars_svc.list_calendar_events(
                    client,
                    calendar_id=self._calendar_filter_id,
                    calendars=cals,
                )
                rli = client.rate_limit_info
                return (events, name_map, cals, rli)
        except APIError as e:
            msg = e.message
            try:
                self.app.call_from_thread(
                    lambda m=msg: self.notify(m, severity="error")
                )
            except Exception:
                pass
            return ([], {}, self._calendars_list or [], None)
        except httpx.TransportError as e:
            notify_transport_error(self, e)
            return ([], {}, self._calendars_list or [], None)

    def _refresh_table(self) -> None:
        table = self.query_one("#calendar-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Start", "End", "Title", "Calendar", "Contact", "Status")
        for ev in self._events:
            cid = ev.get("calendarId") or ""
            cal_label = self._calendar_names.get(
                cid, cid[:12] + "…" if len(cid) > 12 else cid or "—"
            )
            title = (ev.get("title") or "").strip() or "—"
            start_s = _format_event_time(ev.get("startTime"))
            end_s = _format_event_time(ev.get("endTime"))
            contact = (ev.get("contactId") or "").strip() or "—"
            status = (
                ev.get("status")
                or ev.get("appointmentStatus")
                or ev.get("appointment_status")
                or "—"
            ) or "—"
            eid = ev.get("id")
            row_key = str(eid) if eid is not None else None
            table.add_row(
                _cell(start_s),
                _cell(end_s),
                _cell(title),
                _cell(cal_label),
                _cell(contact),
                _cell(status),
                key=row_key,
            )
        table.refresh(layout=True)
        if table.row_count > 0:
            try:
                table.move_cursor(row=0, column=0)
            except Exception:
                pass

    def _update_calendar_select(self) -> None:
        sel = self.query_one("#calendar-select", Select)
        opts: list[tuple[str, str]] = [("All calendars", "")]
        for c in self._calendars_list:
            cid = c.get("id")
            if not cid:
                continue
            opts.append((c.get("name") or cid, cid))
        cur = self._calendar_filter_id or ""
        self._suppress_calendar_select = True
        try:
            sel.set_options(opts)
            valid = {v for (_, v) in opts}
            if cur in valid:
                sel.value = cur
            else:
                sel.value = ""
                self._calendar_filter_id = None
        finally:
            # Defer clearing: Select.Changed can fire after set_options even across frames.
            # call_later(one frame) was not always enough; a short delay avoids a load loop.
            self.set_timer(0.3, self._clear_calendar_select_suppress)

    def action_refresh_calendar(self) -> None:
        calendars_svc.invalidate_location_calendars_cache(get_location_id())
        self.load_events()

    def _get_selected_event(self) -> Optional[dict]:
        table = self.query_one("#calendar-table", DataTable)
        try:
            idx = table.cursor_row
        except Exception:
            return None
        if 0 <= idx < len(self._events):
            return self._events[idx]
        return None

    def _after_modal(self, _: object) -> None:
        self.load_events()

    def action_new_appointment(self) -> None:
        self.app.push_screen(
            CreateAppointmentModal(
                self._calendars_list,
                default_calendar_id=self._calendar_filter_id,
            ),
            self._after_modal,
        )

    def action_edit_appointment(self) -> None:
        ev = self._get_selected_event()
        if not ev:
            self.notify("Select an appointment first", severity="warning")
            return
        eid = ev.get("id")
        if not eid:
            self.notify("Missing appointment id", severity="warning")
            return
        self.app.push_screen(EditAppointmentModal(str(eid)), self._after_modal)

    def action_delete_appointment(self) -> None:
        ev = self._get_selected_event()
        if not ev:
            self.notify("Select an appointment first", severity="warning")
            return
        eid = ev.get("id")
        if not eid:
            self.notify("Missing appointment id", severity="warning")
            return
        title = (ev.get("title") or "").strip() or str(eid)
        self.app.push_screen(
            DeleteAppointmentModal(str(eid), label=title),
            self._after_modal,
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-cal-new":
            self.action_new_appointment()
        elif bid == "btn-cal-edit":
            self.action_edit_appointment()
        elif bid == "btn-cal-delete":
            self.action_delete_appointment()

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        # Do not filter by worker.name: Textual may vary naming; this widget only
        # owns load_events workers. Match on the result tuple shape instead.
        if event.state == WorkerState.ERROR:
            err = getattr(event.worker, "error", None)
            if err is not None:
                friendly = transport_error_toast_message(err)
                self.notify(
                    friendly or f"Calendar load failed: {err}", severity="error"
                )
            return
        if event.state != WorkerState.SUCCESS:
            return
        result = event.worker.result
        if not isinstance(result, tuple) or len(result) != 4:
            return
        events_list, name_map, cals, rli = result
        try:
            header = self.screen.query_one("#header_bar", HeaderBar)
            header.update_rate_limit(rli)
        except Exception:
            pass
        self._calendars_list = cals
        self._calendar_names = name_map
        self._events = events_list
        self._update_calendar_select()
        self._refresh_table()
        try:
            meta = self.query_one("#calendar-meta", Static)
            meta.update(f"[dim]{len(self._events)} event(s)[/dim]")
        except Exception:
            pass
