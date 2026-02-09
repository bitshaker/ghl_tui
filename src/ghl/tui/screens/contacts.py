"""Contacts list and detail view (widget for main screen content)."""

from __future__ import annotations

from typing import Optional

from textual import work
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
)
from textual.worker import Worker, WorkerState

from ...auth import get_location_id, get_token
from ...client import GHLClient
from ...services import contacts as contact_svc
from ..contact_edit import ContactEditModal
from ..contact_notes import ContactNotesModal
from ..contact_opportunities import ContactOpportunitiesModal
from ..contact_tag import AddTagModal, RemoveTagModal


def _contact_label(c: dict) -> str:
    name = (c.get("firstName") or "") + " " + (c.get("lastName") or "")
    name = name.strip() or c.get("name") or c.get("email") or c.get("id") or "—"
    return name[:40].strip()


class ContactDetail(Static):
    """Right-hand panel showing selected contact details."""

    DEFAULT_CSS = """
    ContactDetail {
        width: 1fr;
        padding: 1 2;
        border: solid $primary-darken-2;
        background: $surface-darken-1;
        height: auto;
    }
    .detail-line { padding: 0 0 1 0; }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("Select a contact", **kwargs)
        self._contact: Optional[dict] = None
        self._contact_id: Optional[str] = None

    def show_contact(self, contact: dict) -> None:
        self._contact = contact
        self._contact_id = contact.get("id")
        lines = [
            f"[bold]{_contact_label(contact)}[/bold]  ({contact.get('id', '')})",
            f"email: {contact.get('email') or '—'}",
            f"phone: {contact.get('phone') or '—'}",
            f"company: {contact.get('companyName') or '—'}",
            f"tags: {', '.join(contact.get('tags') or []) or '—'}",
            "",
            "[dim]a[/] add tag  [dim]r[/] remove tag  [dim]N[/] notes  [dim]e[/] edit  [dim]o[/] opportunities",
        ]
        self.update("\n".join(lines))

    def clear_contact(self) -> None:
        self._contact = None
        self._contact_id = None
        self.update("Select a contact")

    @property
    def contact_id(self) -> Optional[str]:
        return self._contact_id

    @property
    def contact(self) -> Optional[dict]:
        return self._contact


class ContactsView(Container):
    """Contacts browse, search, and detail panel."""

    BINDINGS = [
        ("n", "new_contact", "New"),
        ("e", "edit_contact", "Edit"),
        ("a", "add_tag", "Add tag"),
        ("r", "remove_tag", "Remove tag"),
        ("N", "notes", "Notes"),
        ("o", "opportunities", "Opportunities"),
        ("/", "focus_search", "Search"),
    ]

    DEFAULT_CSS = """
    ContactsView {
        width: 100%;
        height: auto;
        layout: horizontal;
    }
    #contacts-left {
        width: 40%;
        height: auto;
        min-width: 24;
        border: solid $primary-darken-2;
        padding: 1;
    }
    #contacts-list {
        height: 1fr;
        min-height: 8;
    }
    #contacts-right {
        width: 1fr;
        height: auto;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._contacts: list[dict] = []
        self._selected_index: int = 0

    def compose(self):
        with Vertical(id="contacts-left"):
            yield Input(placeholder="Search contacts…", id="contacts-search")
            yield ListView(id="contacts-list")
        with Vertical(id="contacts-right"):
            yield ContactDetail(id="contact-detail")

    def on_mount(self) -> None:
        self.load_contacts()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self._selected_index = event.list_view.index
        if 0 <= self._selected_index < len(self._contacts):
            contact = self._contacts[self._selected_index]
            self.load_contact_detail(contact.get("id"))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "contacts-search":
            self.load_contacts(query=event.value or None)

    @work(thread=True)
    def load_contacts(self, query: Optional[str] = None) -> tuple[list[dict], object]:
        with GHLClient(get_token(), get_location_id()) as client:
            contacts = contact_svc.list_contacts(client, limit=50, query=query)
            rli = client.rate_limit_info
            return (contacts, rli)

    @work(thread=True)
    def load_contact_detail(self, contact_id: str) -> tuple[dict, object]:
        with GHLClient(get_token(), get_location_id()) as client:
            contact = contact_svc.get_contact(client, contact_id)
            rli = client.rate_limit_info
            return (contact, rli)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state != WorkerState.SUCCESS or not event.worker.result:
            return
        try:
            header = self.screen.query_one("#header_bar")
            header.update_rate_limit(None)
        except Exception:
            pass
        result = event.worker.result
        if isinstance(result, tuple) and len(result) == 2:
            data, rli = result
            try:
                header = self.screen.query_one("#header_bar")
                header.update_rate_limit(rli)
            except Exception:
                pass
            if isinstance(data, list):
                self._contacts = data
                self._refresh_list()
            elif isinstance(data, dict) and data.get("id"):
                self.query_one("#contact-detail", ContactDetail).show_contact(data)

    def _refresh_list(self) -> None:
        lst = self.query_one("#contacts-list", ListView)
        lst.clear()
        for c in self._contacts:
            lst.append(ListItem(_contact_label(c)))
        if self._contacts:
            lst.index = 0
            self.load_contact_detail(self._contacts[0]["id"])

    def action_focus_search(self) -> None:
        self.query_one("#contacts-search", Input).focus()

    def action_new_contact(self) -> None:
        def on_done(data: dict | None) -> None:
            if data:
                self.load_contacts()

        self.app.push_screen(ContactEditModal(contact=None), on_done)

    def action_edit_contact(self) -> None:
        detail = self.query_one("#contact-detail", ContactDetail)
        if not detail.contact_id:
            self.notify("Select a contact first", severity="warning")
            return
        cid = detail.contact_id

        def on_done(data: dict | None) -> None:
            if data:
                self.load_contact_detail(cid)
                self.load_contacts()

        self.app.push_screen(ContactEditModal(contact=detail.contact), on_done)

    def action_add_tag(self) -> None:
        detail = self.query_one("#contact-detail", ContactDetail)
        if not detail.contact_id:
            self.notify("Select a contact first", severity="warning")
            return
        self.app.push_screen(AddTagModal(detail.contact_id))

    def action_remove_tag(self) -> None:
        detail = self.query_one("#contact-detail", ContactDetail)
        if not detail.contact_id or not (detail.contact and (detail.contact.get("tags"))):
            self.notify("Select a contact with tags first", severity="warning")
            return
        self.app.push_screen(RemoveTagModal(detail.contact_id, detail.contact.get("tags", [])))

    def action_notes(self) -> None:
        detail = self.query_one("#contact-detail", ContactDetail)
        if not detail.contact_id:
            self.notify("Select a contact first", severity="warning")
            return
        self.app.push_screen(ContactNotesModal(detail.contact_id))

    def action_opportunities(self) -> None:
        detail = self.query_one("#contact-detail", ContactDetail)
        if not detail.contact_id:
            self.notify("Select a contact first", severity="warning")
            return
        self.app.push_screen(ContactOpportunitiesModal(detail.contact_id))
