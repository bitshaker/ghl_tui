"""Contact notes modal: list notes and add a new one."""

from __future__ import annotations

from datetime import datetime

from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, RichLog, TextArea

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..services import contacts as contact_svc


def format_note_date(date_added: str) -> str:
    """Format API datetime (e.g. 2026-02-09T21:38:48Z) for display."""
    if not date_added:
        return ""
    raw = date_added.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw[:19])
        return dt.strftime("%b %d, %Y at %I:%M %p")
    except (ValueError, TypeError):
        return date_added[:19] if len(date_added) >= 19 else date_added


class ContactNotesModal(ModalScreen[None]):
    """Modal showing notes for a contact and allowing add."""

    CSS = """
    #note-input {
        height: 6;
    }
    """

    def __init__(self, contact_id: str, contact_name: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._contact_id = contact_id
        self._contact_name = (contact_name or "").strip() or None

    def compose(self):
        with Vertical():
            if self._contact_name:
                yield Label(f"Notes — {self._contact_name}", id="notes-title")
            else:
                yield Label("Notes", id="notes-title")
            yield RichLog(id="notes-log", highlight=True, markup=True)
            yield TextArea(id="note-input")
            yield Button("Add note", id="note-add")
            yield Button("Close", id="notes-close")

    def on_mount(self) -> None:
        self._load_notes()

    def _load_notes(self) -> None:
        with GHLClient(get_token(), get_location_id()) as client:
            notes = contact_svc.list_notes(client, self._contact_id)
        log = self.query_one("#notes-log", RichLog)
        log.clear()
        for i, n in enumerate(notes):
            body = n.get("body") or ""
            date_str = format_note_date(n.get("dateAdded") or "")
            if date_str:
                log.write(f"[dim]{date_str}[/dim]\n{body}")
            else:
                log.write(body)
            if i < len(notes) - 1:
                log.write("\n[dim]─────────────────────────────[/dim]\n")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "notes-close":
            self.dismiss(None)
        elif event.button.id == "note-add":
            text_area = self.query_one("#note-input", TextArea)
            text = text_area.text.strip()
            if not text:
                return
            with GHLClient(get_token(), get_location_id()) as client:
                contact_svc.add_note(client, self._contact_id, text)
            text_area.clear()
            self._load_notes()
            self.app.notify("Note added")
