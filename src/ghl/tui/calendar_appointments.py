"""Modals for creating, editing, and deleting calendar appointments in the TUI."""

from __future__ import annotations

import time
from datetime import date, datetime, time as time_cls, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from textual import on
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListItem, ListView, Select, Static, TextArea

from ..auth import get_location_id, get_token
from ..client import APIError, GHLClient
from ..services import calendars as calendars_svc
from ..services import contacts as contact_svc


# Hour / minute dropdowns (calendar timezone on submit; see slot_iso_in_calendar_tz)
SLOT_HOUR_OPTIONS: list[tuple[str, str]] = [(f"{h:02d}", f"{h:02d}") for h in range(24)]
SLOT_MINUTE_OPTIONS: list[tuple[str, str]] = [
    ("00", "00"),
    ("15", "15"),
    ("30", "30"),
    ("45", "45"),
]


def _snap_minute_to_quarter(minute: int) -> str:
    best = min((0, 15, 30, 45), key=lambda q: abs(q - minute))
    return f"{best:02d}"


def slot_iso_in_calendar_tz(date_str: str, hour: str, minute: str, tz_name: str) -> tuple[str, str]:
    """
    Build selectedSlot (ISO 8601 with offset) and selectedTimezone for GHL booking.

    The slot must be expressed in the calendar's IANA timezone; the API validates
    availability against that zone (see create appointment docs).
    """
    d = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    h = int(hour)
    mi = int(minute)
    if not (0 <= h <= 23 and 0 <= mi <= 59):
        raise ValueError("Invalid time")
    safe_tz = (tz_name or "").strip() or "UTC"
    try:
        tz = ZoneInfo(safe_tz)
    except Exception:
        tz = ZoneInfo("UTC")
        safe_tz = "UTC"
    combined = datetime.combine(d, time_cls(hour=h, minute=mi), tzinfo=tz)
    return combined.isoformat(timespec="seconds"), safe_tz


def parse_iso_to_date_hour_min_in_tz(iso_str: str, tz_name: str) -> tuple[str, str, str]:
    """Parse API datetime to (YYYY-MM-DD, HH, MM) in the given IANA zone; MM is quarter-snapped."""
    s = (iso_str or "").strip()
    if not s:
        return date.today().isoformat(), "09", "00"
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        if "T" in s:
            dt = datetime.fromisoformat(s)
        else:
            dt = datetime.fromisoformat(s[:10]).replace(tzinfo=timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        try:
            cal_tz = ZoneInfo((tz_name or "UTC").strip() or "UTC")
        except Exception:
            cal_tz = ZoneInfo("UTC")
        local = dt.astimezone(cal_tz)
        return (
            local.strftime("%Y-%m-%d"),
            f"{local.hour:02d}",
            _snap_minute_to_quarter(local.minute),
        )
    except (ValueError, TypeError):
        return date.today().isoformat(), "09", "00"


def _valid_select_value(value: object, options: list[tuple[str, str]], fallback: str) -> str:
    """Return a value that exists in options (second element), else fallback."""
    if value is None:
        return fallback
    s = str(value).strip()
    valid = {v for (_, v) in options}
    return s if s in valid else fallback


def _contact_row_label(contact: dict) -> str:
    """Single-line label for pick lists."""
    fn = (contact.get("firstName") or "").strip()
    ln = (contact.get("lastName") or "").strip()
    name = f"{fn} {ln}".strip() or (contact.get("name") or "").strip() or "—"
    email = (contact.get("email") or "").strip() or ""
    phone = (contact.get("phone") or "").strip() or ""
    parts = [name]
    if email:
        parts.append(email)
    if phone:
        parts.append(phone)
    line = " · ".join(parts)
    return (line[:85] + "…") if len(line) > 85 else line


class CreateAppointmentModal(ModalScreen[None]):
    """Create an appointment (POST /calendars/events/appointments)."""

    CSS = """
    CreateAppointmentModal {
        align: center middle;
    }
    CreateAppointmentModal > Vertical {
        width: 92;
        min-width: 56;
        height: auto;
    }
    #appt-create-notes {
        height: 4;
        width: 100%;
    }
    #appt-contact-block {
        height: auto;
    }
    #appt-contact-search-row {
        height: auto;
        max-height: 3;
        margin-bottom: 0;
    }
    #appt-contact-list {
        height: 8;
        max-height: 8;
        margin-top: 0;
        border: tall $primary;
    }
    #appt-slot-block {
        height: auto;
        margin-top: 0;
        margin-bottom: 1;
    }
    #appt-slot-row-date, #appt-slot-row-time {
        height: auto;
        min-height: 3;
    }
    .slot-field-label {
        width: 8;
        min-width: 8;
    }
    #appt-slot-date {
        width: 24;
        min-width: 20;
    }
    #appt-slot-hour {
        width: 10;
        min-width: 10;
    }
    #appt-slot-min {
        width: 10;
        min-width: 10;
    }
    #appt-slot-colon {
        width: 3;
        min-width: 3;
        content-align: center middle;
    }
    """

    def __init__(
        self,
        calendars: list[dict],
        *,
        default_calendar_id: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._calendars = calendars
        self._default_calendar_id = (default_calendar_id or "").strip() or None
        self._contact_results: list[dict] = []
        self._selected_contact_id: Optional[str] = None
        self._last_contact_search_at: float = 0.0

    def compose(self):
        with Vertical():
            yield Label("New appointment")
            if not self._calendars:
                yield Static("No calendars in this location. Add one in GoHighLevel first.")
                yield Button("Close", id="appt-create-close")
                return
            opts = [
                (c.get("name") or c.get("id") or "—", c["id"])
                for c in self._calendars
                if c.get("id")
            ]
            default_val = self._default_calendar_id
            if default_val and not any(cid == default_val for (_, cid) in opts):
                default_val = opts[0][1]
            elif not default_val:
                default_val = opts[0][1]
            yield Label("Calendar")
            yield Select(opts, value=default_val, id="appt-create-cal")
            with Vertical(id="appt-contact-block"):
                yield Label("Contact *")
                yield Static(
                    "[dim]Press Search to load contacts (empty query = first 50), then pick one.[/dim]",
                    id="appt-contact-selected",
                )
                with Horizontal(id="appt-contact-search-row"):
                    yield Input(
                        placeholder="Search name, email, phone…",
                        id="appt-contact-search",
                    )
                    yield Button("Search", id="appt-contact-search-btn", variant="primary")
                yield ListView(id="appt-contact-list")
            yield Label("Slot (wall time) *")
            with Vertical(id="appt-slot-block"):
                with Horizontal(id="appt-slot-row-date"):
                    yield Label("Date", classes="slot-field-label")
                    yield Input(placeholder="YYYY-MM-DD", id="appt-slot-date")
                with Horizontal(id="appt-slot-row-time"):
                    yield Label("Time", classes="slot-field-label")
                    yield Select(SLOT_HOUR_OPTIONS, value="09", id="appt-slot-hour")
                    yield Label(":", id="appt-slot-colon")
                    yield Select(SLOT_MINUTE_OPTIONS, value="00", id="appt-slot-min")
                yield Static(
                    "[dim]Times use this calendar's zone (or location if omitted).[/dim]",
                    id="appt-slot-tz-hint",
                )
            yield Label("Title")
            yield Input(placeholder="Optional", id="appt-create-title")
            yield Label("Notes")
            yield TextArea(placeholder="Optional…", id="appt-create-notes")
            with Horizontal():
                yield Button("Create", variant="primary", id="appt-create-submit")
                yield Button("Cancel", id="appt-create-cancel")

    def on_mount(self) -> None:
        if not self._calendars:
            return
        self.call_later(self._init_create_form)

    def _init_create_form(self) -> None:
        try:
            self.query_one("#appt-slot-date", Input).value = date.today().isoformat()
        except Exception:
            pass
        self._contact_results = []
        self._refresh_contact_list()
        self._update_slot_tz_hint()
        try:
            self.query_one("#appt-contact-search", Input).focus()
        except Exception:
            pass

    def _update_slot_tz_hint(self) -> None:
        try:
            hint = self.query_one("#appt-slot-tz-hint", Static)
        except Exception:
            return
        if not self._calendars:
            return
        try:
            sel = self.query_one("#appt-create-cal", Select)
            raw = sel.value
            cal_id = (raw or "").strip() if isinstance(raw, str) else ""
        except Exception:
            cal_id = ""
        if not cal_id:
            hint.update(
                "[dim]Times use this calendar's zone (or location if omitted).[/dim]"
            )
            return
        try:
            with GHLClient(get_token(), get_location_id()) as client:
                tz_name = calendars_svc.resolve_calendar_timezone(client, cal_id, self._calendars)
        except APIError:
            hint.update("[dim]Could not load timezone; booking may use UTC.[/dim]")
            return
        hint.update(
            f"[dim]Booking uses IANA timezone:[/dim] [bold]{tz_name}[/bold] "
            f"[dim](enter the start time as wall clock in that zone.)[/dim]"
        )

    @on(Select.Changed, "#appt-create-cal")
    def on_create_calendar_changed(self, event: Select.Changed) -> None:
        self._update_slot_tz_hint()

    def _run_contact_search(self) -> None:
        now = time.monotonic()
        if now - self._last_contact_search_at < 0.8:
            self.app.notify("Wait a moment between contact searches.", severity="warning")
            return
        self._last_contact_search_at = now
        q = self.query_one("#appt-contact-search", Input).value.strip()
        try:
            with GHLClient(get_token(), get_location_id()) as client:
                if q:
                    contacts = contact_svc.search_contacts(client, q, limit=50)
                else:
                    contacts = contact_svc.list_contacts(client, limit=50)
        except APIError as e:
            self.app.notify(e.message, severity="error")
            return
        self._contact_results = contacts
        self._selected_contact_id = None
        self._refresh_contact_list()
        self._update_contact_selected_static()

    def _refresh_contact_list(self) -> None:
        lst = self.query_one("#appt-contact-list", ListView)
        lst.clear()
        for c in self._contact_results:
            cid = c.get("id")
            if not cid:
                continue
            lst.append(ListItem(Label(_contact_row_label(c))))

    def _update_contact_selected_static(self) -> None:
        try:
            sel = self.query_one("#appt-contact-selected", Static)
        except Exception:
            return
        if self._selected_contact_id:
            c = next(
                (x for x in self._contact_results if x.get("id") == self._selected_contact_id),
                None,
            )
            if c:
                sel.update(f"[bold]Selected:[/bold] {_contact_row_label(c)}")
            else:
                sel.update(f"[bold]Selected id:[/bold] {self._selected_contact_id}")
        else:
            sel.update(
                "[dim]Press Search to load contacts (empty query = first 50), then pick one.[/dim]"
            )

    @on(Input.Submitted)
    def on_search_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "appt-contact-search":
            self._run_contact_search()

    @on(ListView.Selected, "#appt-contact-list")
    def on_contact_list_selected(self, event: ListView.Selected) -> None:
        try:
            idx = event.list_view.index
        except (AttributeError, IndexError, RuntimeError):
            return
        if idx is None or idx < 0:
            return
        if idx >= len(self._contact_results):
            return
        cid = self._contact_results[idx].get("id")
        self._selected_contact_id = str(cid) if cid else None
        self._update_contact_selected_static()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "appt-contact-search-btn":
            self._run_contact_search()
            return
        if event.button.id in ("appt-create-cancel", "appt-create-close"):
            self.dismiss(None)
            return
        if event.button.id != "appt-create-submit":
            return
        if not self._calendars:
            self.dismiss(None)
            return
        contact_id = (self._selected_contact_id or "").strip()
        if not contact_id:
            self.app.notify("Select a contact and enter a slot time", severity="warning")
            return
        cal_id = self.query_one("#appt-create-cal", Select).value
        cal_id = (cal_id or "").strip()
        if not cal_id:
            self.app.notify("Select a calendar", severity="warning")
            return
        date_str = self.query_one("#appt-slot-date", Input).value.strip()
        hour_s = _valid_select_value(
            self.query_one("#appt-slot-hour", Select).value,
            SLOT_HOUR_OPTIONS,
            "09",
        )
        min_s = _valid_select_value(
            self.query_one("#appt-slot-min", Select).value,
            SLOT_MINUTE_OPTIONS,
            "00",
        )
        title = self.query_one("#appt-create-title", Input).value.strip() or None
        notes = self.query_one("#appt-create-notes", TextArea).text.strip() or None
        location_id = get_location_id()
        try:
            with GHLClient(get_token(), location_id) as client:
                tz_name = calendars_svc.resolve_calendar_timezone(client, cal_id, self._calendars)
                try:
                    slot_iso, sel_tz = slot_iso_in_calendar_tz(date_str, hour_s, min_s, tz_name)
                except ValueError:
                    self.app.notify("Invalid date or time", severity="warning")
                    return
                data = {
                    "calendarId": cal_id,
                    "contactId": contact_id,
                    "selectedSlot": slot_iso,
                    "selectedTimezone": sel_tz,
                    "locationId": location_id,
                }
                if title:
                    data["title"] = title
                if notes:
                    data["notes"] = notes
                client.post("/calendars/events/appointments", json=data)
        except APIError as e:
            self.app.notify(e.message, severity="error")
            return
        self.app.notify("Appointment created")
        calendars_svc.invalidate_location_calendars_cache(location_id)
        self.dismiss(None)


class EditAppointmentModal(ModalScreen[None]):
    """Update an appointment (PUT /calendars/events/appointments/:id)."""

    CSS = """
    EditAppointmentModal {
        align: center middle;
    }
    EditAppointmentModal > Vertical {
        width: 92;
        min-width: 56;
        height: auto;
    }
    #appt-edit-notes {
        height: 4;
        width: 100%;
    }
    #appt-edit-slot-block {
        height: auto;
        margin-bottom: 1;
    }
    #appt-edit-slot-row-date, #appt-edit-slot-row-time {
        height: auto;
        min-height: 3;
    }
    #appt-edit-slot-date {
        width: 24;
        min-width: 20;
    }
    #appt-edit-slot-hour {
        width: 10;
        min-width: 10;
    }
    #appt-edit-slot-min {
        width: 10;
        min-width: 10;
    }
    #appt-edit-slot-colon {
        width: 3;
        min-width: 3;
    }
    EditAppointmentModal .slot-field-label {
        width: 8;
        min-width: 8;
    }
    """

    def __init__(self, appointment_id: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._appointment_id = appointment_id
        self._calendar_tz = "UTC"

    def compose(self):
        with Vertical():
            yield Label("Edit appointment")
            yield Static("Loading…", id="appt-edit-loading")
            yield Label("Start (wall time in calendar / location zone)")
            with Vertical(id="appt-edit-slot-block"):
                with Horizontal(id="appt-edit-slot-row-date"):
                    yield Label("Date", classes="slot-field-label")
                    yield Input(placeholder="YYYY-MM-DD", id="appt-edit-slot-date")
                with Horizontal(id="appt-edit-slot-row-time"):
                    yield Label("Time", classes="slot-field-label")
                    yield Select(SLOT_HOUR_OPTIONS, value="09", id="appt-edit-slot-hour")
                    yield Label(":", id="appt-edit-slot-colon")
                    yield Select(SLOT_MINUTE_OPTIONS, value="00", id="appt-edit-slot-min")
            yield Label("Title")
            yield Input(id="appt-edit-title")
            yield Label("Notes")
            yield TextArea(id="appt-edit-notes")
            yield Label("Status (optional)")
            yield Input(id="appt-edit-appt-status", placeholder="e.g. confirmed, cancelled")
            with Horizontal():
                yield Button("Save", variant="primary", id="appt-edit-save")
                yield Button("Cancel", id="appt-edit-cancel")

    def on_mount(self) -> None:
        self.call_later(self._load_appointment)

    def _load_appointment(self) -> None:
        try:
            with GHLClient(get_token(), get_location_id()) as client:
                r = client.get(
                    f"/calendars/events/appointments/{self._appointment_id}",
                    include_location_id=False,
                )
                appt = r.get("appointment", r.get("event", r))
                cal_id = (appt.get("calendarId") or "").strip()
                self._calendar_tz = (
                    calendars_svc.resolve_calendar_timezone(client, cal_id, None)
                    if cal_id
                    else "UTC"
                )
        except APIError as e:
            self.app.notify(e.message, severity="error")
            self.dismiss(None)
            return
        self.query_one("#appt-edit-loading", Static).display = False
        ds, hs, ms = parse_iso_to_date_hour_min_in_tz(
            appt.get("startTime") or "", self._calendar_tz
        )
        self.query_one("#appt-edit-slot-date", Input).value = ds
        try:
            self.query_one("#appt-edit-slot-hour", Select).value = _valid_select_value(
                hs, SLOT_HOUR_OPTIONS, "09"
            )
            self.query_one("#appt-edit-slot-min", Select).value = _valid_select_value(
                ms, SLOT_MINUTE_OPTIONS, "00"
            )
        except (ValueError, AttributeError):
            self.query_one("#appt-edit-slot-hour", Select).value = "09"
            self.query_one("#appt-edit-slot-min", Select).value = "00"
        self.query_one("#appt-edit-title", Input).value = (appt.get("title") or "").strip()
        self.query_one("#appt-edit-notes", TextArea).text = (appt.get("notes") or "").strip()
        self.query_one("#appt-edit-appt-status", Input).value = (
            (appt.get("status") or appt.get("appointmentStatus") or "").strip()
        )
        self.query_one("#appt-edit-slot-date", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "appt-edit-cancel":
            self.dismiss(None)
            return
        if event.button.id != "appt-edit-save":
            return
        try:
            slot_iso, sel_tz = slot_iso_in_calendar_tz(
                self.query_one("#appt-edit-slot-date", Input).value.strip(),
                _valid_select_value(
                    self.query_one("#appt-edit-slot-hour", Select).value,
                    SLOT_HOUR_OPTIONS,
                    "09",
                ),
                _valid_select_value(
                    self.query_one("#appt-edit-slot-min", Select).value,
                    SLOT_MINUTE_OPTIONS,
                    "00",
                ),
                self._calendar_tz,
            )
        except ValueError:
            self.app.notify("Invalid date or time", severity="warning")
            return
        title = self.query_one("#appt-edit-title", Input).value.strip()
        notes = self.query_one("#appt-edit-notes", TextArea).text.strip()
        status = self.query_one("#appt-edit-appt-status", Input).value.strip()
        data: dict = {"selectedSlot": slot_iso, "selectedTimezone": sel_tz}
        if title:
            data["title"] = title
        if notes:
            data["notes"] = notes
        if status:
            data["status"] = status
        try:
            with GHLClient(get_token(), get_location_id()) as client:
                client.put(
                    f"/calendars/events/appointments/{self._appointment_id}",
                    json=data,
                    include_location_id=False,
                )
        except APIError as e:
            self.app.notify(e.message, severity="error")
            return
        self.app.notify("Appointment updated")
        self.dismiss(None)


class DeleteAppointmentModal(ModalScreen[None]):
    """Confirm delete for DELETE /calendars/events/appointments/:id."""

    def __init__(self, appointment_id: str, *, label: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._appointment_id = appointment_id
        self._label = label or appointment_id

    def compose(self):
        with Vertical():
            yield Label("Delete appointment?")
            yield Label(self._label, id="appt-del-label")
            with Horizontal():
                yield Button("Delete", variant="error", id="appt-del-confirm")
                yield Button("Cancel", id="appt-del-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "appt-del-cancel":
            self.dismiss(None)
            return
        if event.button.id != "appt-del-confirm":
            return
        try:
            with GHLClient(get_token(), get_location_id()) as client:
                client.delete(
                    f"/calendars/events/appointments/{self._appointment_id}",
                    include_location_id=False,
                )
        except APIError as e:
            self.app.notify(e.message, severity="error")
            return
        self.app.notify("Appointment deleted")
        self.dismiss(None)
