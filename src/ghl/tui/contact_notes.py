"""Contact notes modal: list notes and add a new one."""

from __future__ import annotations

from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, RichLog, Static

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..services import contacts as contact_svc


class ContactNotesModal(ModalScreen[None]):
    """Modal showing notes for a contact and allowing add."""

    def __init__(self, contact_id: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._contact_id = contact_id

    def compose(self):
        with Vertical():
            yield Label("Notes")
            yield RichLog(id="notes-log", highlight=True)
            yield Input(placeholder="New note…", id="note-input")
            yield Button("Add note", id="note-add")
            yield Button("Close", id="notes-close")

    def on_mount(self) -> None:
        self._load_notes()

    def _load_notes(self) -> None:
        with GHLClient(get_token(), get_location_id()) as client:
            notes = contact_svc.list_notes(client, self._contact_id)
        log = self.query_one("#notes-log", RichLog)
        log.clear()
        for n in notes:
            body = (n.get("body") or "").replace("\n", " ")
            date = n.get("dateAdded", "")[:19] if n.get("dateAdded") else ""
            log.write(f"[dim]{date}[/dim] {body}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "notes-close":
            self.dismiss(None)
        elif event.button.id == "note-add":
            inp = self.query_one("#note-input", Input)
            text = inp.value.strip()
            if not text:
                return
            with GHLClient(get_token(), get_location_id()) as client:
                contact_svc.add_note(client, self._contact_id, text)
            inp.clear()
            self._load_notes()
            self.app.notify("Note added")
