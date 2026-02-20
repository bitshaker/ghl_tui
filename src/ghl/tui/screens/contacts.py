"""Contacts list and detail view (widget for main screen content)."""

from __future__ import annotations

from typing import Any, Optional

from textual import work
from textual.containers import Container, Vertical
from textual.widgets import (
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
from ...services import custom_fields as custom_fields_svc
from ...services import users as users_svc
from ..contact_edit import ContactEditModal
from ..contact_filter import ContactFilterModal, SavedSearchesModal
from ..contact_notes import ContactNotesModal, format_note_date
from ..contact_opportunities import ContactOpportunitiesModal
from ..contact_tag import AddTagModal, RemoveTagModal
from ..contact_tasks import ContactTasksModal, task_display_text
from ..text_utils import html_to_plain


def _contact_label(c: dict) -> str:
    name = (c.get("firstName") or "") + " " + (c.get("lastName") or "")
    name = name.strip() or c.get("name") or c.get("email") or c.get("id") or "—"
    return name[:40].strip().title()


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
        self._custom_field_defs: list[dict] = []
        self._custom_values: list[dict] = []
        self._custom_values_map: dict[str, str] = {}
        self._custom_value_id_map: dict[str, str] = {}

    def show_contact(
        self,
        contact: dict,
        custom_field_defs: Optional[list[dict]] = None,
        custom_values: Optional[list[dict]] = None,
    ) -> None:
        self._contact = contact
        self._contact_id = contact.get("id")
        self._custom_field_defs = custom_field_defs or []
        self._custom_values = custom_values or []
        self._custom_values_map = custom_fields_svc.build_custom_values_map(
            contact, self._custom_values, self._custom_field_defs
        )
        self._custom_value_id_map = custom_fields_svc.build_custom_value_id_map(
            self._custom_values
        )

        field_id_to_name = {
            str(f.get("id") or f.get("customFieldId", "")): f.get("name") or f.get("label", "?")
            for f in self._custom_field_defs
        }
        custom_lines = []
        for fid, val in self._custom_values_map.items():
            name = field_id_to_name.get(fid, fid)
            if name and name != "?":
                custom_lines.append(f"{name}: {val or '—'}")

        lines = [
            f"[bold]{_contact_label(contact)}[/bold]  ({contact.get('id', '')})",
            f"email: {contact.get('email') or '—'}",
            f"phone: {contact.get('phone') or '—'}",
            f"company: {contact.get('companyName') or '—'}",
            f"tags: {', '.join(contact.get('tags') or []) or '—'}",
        ]
        if custom_lines:
            lines.append("")
            lines.extend(custom_lines)
        lines.extend([
            "",
            "[dim]n[/] notes  [dim]t[/] tasks  [dim]N[/] new  [dim]a[/] add  [dim]r[/] remove tag",
            "[dim]e[/] edit  [dim]o[/] opportunities  [dim]R[/] refresh",
        ])
        self.update("\n".join(lines))

    def clear_contact(self) -> None:
        self._contact = None
        self._contact_id = None
        self._custom_field_defs = []
        self._custom_values = []
        self._custom_values_map = {}
        self._custom_value_id_map = {}
        self.update("Select a contact")

    @property
    def contact_id(self) -> Optional[str]:
        return self._contact_id

    @property
    def contact(self) -> Optional[dict]:
        return self._contact

    @property
    def custom_field_defs(self) -> list[dict]:
        return self._custom_field_defs

    @property
    def custom_values_map(self) -> dict[str, str]:
        return self._custom_values_map

    @property
    def custom_value_id_map(self) -> dict[str, str]:
        return self._custom_value_id_map


class ContactNotesPreview(Static):
    """Shows a preview of notes for the selected contact below the main detail."""

    DEFAULT_CSS = """
    ContactNotesPreview {
        width: 1fr;
        padding: 1 2;
        border: solid $primary-darken-2;
        border-top: none;
        background: $surface-darken-2;
        height: auto;
        max-height: 12;
        overflow-y: auto;
    }
    """

    def show_notes(self, notes: list[dict]) -> None:
        """Update content with the given notes (list of dicts with body, dateAdded)."""
        if not notes:
            self.update("[dim]No notes. Press n to add one.[/dim]")
            return
        lines = ["[bold]Notes[/bold]", ""]
        for i, n in enumerate(notes):
            body = html_to_plain(n.get("body") or "").replace("\n", " ")
            date_str = format_note_date(n.get("dateAdded") or "")
            if date_str:
                lines.append(f"[dim]{date_str}[/dim]")
            lines.append(body)
            if i < len(notes) - 1:
                lines.append("[dim]─────────────────────────────[/dim]")
                lines.append("")
        self.update("\n".join(lines))

    def clear_notes(self) -> None:
        """Clear the notes preview (no contact selected)."""
        self.update("")


class ContactTasksPreview(Static):
    """Shows a preview of tasks for the selected contact below the detail."""

    DEFAULT_CSS = """
    ContactTasksPreview {
        width: 1fr;
        padding: 1 2;
        border: solid $primary-darken-2;
        border-top: none;
        background: $surface-darken-2;
        height: auto;
        max-height: 10;
        overflow-y: auto;
    }
    """

    def show_tasks(self, tasks: list[dict]) -> None:
        """Update content with the given tasks."""
        if not tasks:
            self.update("[dim]No tasks. Press t to manage.[/dim]")
            return
        lines = ["[bold]Tasks[/bold]", ""]
        for i, t in enumerate(tasks):
            lines.append(task_display_text(t))
            if i < len(tasks) - 1:
                lines.append("[dim]─────────────────────────────[/dim]")
        self.update("\n".join(lines))

    def clear_tasks(self) -> None:
        """Clear the tasks preview (no contact selected)."""
        self.update("")


class ContactsView(Container):
    """Contacts browse, search, and detail panel."""

    BINDINGS = [
        ("n", "notes", "Notes"),
        ("t", "tasks", "Tasks"),
        ("N", "new_contact", "New"),
        ("e", "edit_contact", "Edit"),
        ("a", "add_tag", "Add tag"),
        ("r", "remove_tag", "Remove tag"),
        ("o", "opportunities", "Opportunities"),
        ("R", "refresh_contacts", "Refresh"),
        ("/", "focus_search", "Search"),
        ("f", "filter_contacts", "Filter"),
        ("s", "saved_searches", "Saved"),
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
        self._current_filter: dict[str, Any] = {}
        self._saved_search_name: Optional[str] = None

    def compose(self):
        with Vertical(id="contacts-left"):
            yield Input(placeholder="Search contacts…", id="contacts-search")
            yield Static("", id="contacts-filter-label")
            yield ListView(id="contacts-list")
        with Vertical(id="contacts-right"):
            yield ContactDetail(id="contact-detail")
            yield ContactTasksPreview(id="contact-tasks-preview")
            yield ContactNotesPreview(id="contact-notes-preview")

    def on_mount(self) -> None:
        self._update_filter_label()
        self.load_contacts()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self._selected_index = event.list_view.index
        if 0 <= self._selected_index < len(self._contacts):
            contact = self._contacts[self._selected_index]
            self.load_contact_detail(contact.get("id"))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "contacts-search":
            self.load_contacts()

    def _filter_label(self) -> str:
        if self._saved_search_name:
            return f"[dim]Saved: {self._saved_search_name}[/dim]"
        f = self._current_filter
        parts = []
        if f.get("tags"):
            parts.append(f"tags: {', '.join(f['tags'])}")
        if f.get("assignedTo"):
            parts.append("assigned")
        if f.get("query"):
            parts.append(f"q: {f['query']}")
        if not parts:
            return ""
        return "[dim]" + " | ".join(parts) + "[/dim]"

    def _update_filter_label(self) -> None:
        try:
            self.query_one("#contacts-filter-label", Static).update(self._filter_label())
        except Exception:
            pass

    @work(thread=True)
    def load_contacts(self, query_override: Optional[str] = None) -> tuple[list[dict], object]:
        location_id = get_location_id()
        with GHLClient(get_token(), location_id) as client:
            query = query_override
            if query is None:
                try:
                    inp = self.query_one("#contacts-search", Input)
                    query = (inp.value or "").strip() or None
                except Exception:
                    pass
            if query is None and self._current_filter:
                query = self._current_filter.get("query")
            tags = self._current_filter.get("tags") or []
            assigned_to = self._current_filter.get("assignedTo")
            if tags or assigned_to:
                contacts = contact_svc.contacts_search(
                    client,
                    location_id,
                    page_limit=50,
                    query=query,
                    tags=tags if tags else None,
                    assigned_to=assigned_to,
                )
            else:
                contacts = contact_svc.list_contacts(client, limit=50, query=query)
            rli = client.rate_limit_info
            return (contacts, rli)

    @work(thread=True)
    def load_contact_detail(self, contact_id: str) -> tuple:
        location_id = get_location_id()
        with GHLClient(get_token(), location_id) as client:
            contact = contact_svc.get_contact(client, contact_id)
            notes = contact_svc.list_notes(client, contact_id)
            tasks = contact_svc.list_tasks(client, contact_id)
            custom_field_defs: list[dict] = []
            custom_values: list[dict] = []
            try:
                custom_field_defs = custom_fields_svc.list_custom_fields(client, location_id)
                custom_values = custom_fields_svc.list_custom_values(
                    client, location_id, contact_id
                )
            except Exception:
                pass
            rli = client.rate_limit_info
            return (contact, notes, tasks, custom_field_defs, custom_values, rli)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state != WorkerState.SUCCESS or not event.worker.result:
            return
        try:
            header = self.screen.query_one("#header_bar")
            header.update_rate_limit(None)
        except Exception:
            pass
        result = event.worker.result
        if isinstance(result, tuple) and len(result) >= 4:
            contact = result[0]
            notes = result[1]
            tasks = result[2]
            if len(result) == 6:
                custom_field_defs = result[3]
                custom_values = result[4]
                rli = result[5]
            else:
                custom_field_defs = []
                custom_values = []
                rli = result[3]
            try:
                header = self.screen.query_one("#header_bar")
                header.update_rate_limit(rli)
            except Exception:
                pass
            if isinstance(contact, dict) and contact.get("id"):
                self.query_one("#contact-detail", ContactDetail).show_contact(
                    contact,
                    custom_field_defs=custom_field_defs,
                    custom_values=custom_values,
                )
                self.query_one("#contact-tasks-preview", ContactTasksPreview).show_tasks(tasks)
                self.query_one("#contact-notes-preview", ContactNotesPreview).show_notes(notes)
        elif isinstance(result, tuple) and len(result) == 2:
            data, rli = result
            try:
                header = self.screen.query_one("#header_bar")
                header.update_rate_limit(rli)
            except Exception:
                pass
            if isinstance(data, list):
                self._contacts = data
                if not self._contacts:
                    self.query_one("#contact-detail", ContactDetail).clear_contact()
                    self.query_one("#contact-tasks-preview", ContactTasksPreview).clear_tasks()
                    self.query_one("#contact-notes-preview", ContactNotesPreview).clear_notes()
                self._refresh_list()

    def _refresh_list(self) -> None:
        lst = self.query_one("#contacts-list", ListView)
        lst.clear()
        for c in self._contacts:
            lst.append(ListItem(Label(_contact_label(c))))
        if self._contacts:
            lst.index = 0
            self.load_contact_detail(self._contacts[0]["id"])
        lst.focus()

    def action_focus_search(self) -> None:
        self.query_one("#contacts-search", Input).focus()

    def action_refresh_contacts(self) -> None:
        """Reload the contacts list from the API."""
        self.load_contacts()

    def _apply_filter_result(self, result: Any) -> None:
        if result is None:
            return
        if isinstance(result, tuple) and len(result) == 2:
            self._current_filter = result[0] or {}
            self._saved_search_name = result[1]
        else:
            self._current_filter = result or {}
            self._saved_search_name = None
        self._update_filter_label()
        self.load_contacts()

    def action_filter_contacts(self) -> None:
        """Open filter modal; on apply/save set filter and reload."""
        try:
            with GHLClient(get_token(), get_location_id()) as client:
                users = users_svc.list_users(client)
        except Exception as e:
            self.notify(f"Could not load users: {e}", severity="error")
            users = []
        def on_done(res: Any) -> None:
            self._apply_filter_result(res)
        self.app.push_screen(
            ContactFilterModal(users=users or [], current_filter=self._current_filter),
            on_done,
        )

    def action_saved_searches(self) -> None:
        """Open saved searches modal; on select set filter and reload."""
        def on_done(result: Any) -> None:
            self._apply_filter_result(result)
        self.app.push_screen(SavedSearchesModal(), on_done)

    def action_new_contact(self) -> None:
        def on_done(data: dict | None) -> None:
            if data:
                self.load_contacts()

        location_id = get_location_id()
        users: list[dict] = []
        custom_field_defs: list[dict] = []
        try:
            with GHLClient(get_token(), location_id) as client:
                users = users_svc.list_users(client)
        except Exception as e:
            self.notify(f"Could not load users: {e}", severity="error")
        try:
            with GHLClient(get_token(), location_id) as client:
                custom_field_defs = custom_fields_svc.list_custom_fields(
                    client, location_id
                )
        except Exception:
            pass  # modal still shows standard fields
        self.app.push_screen(
            ContactEditModal(
                contact=None,
                users=users or [],
                custom_field_defs=custom_field_defs or [],
            ),
            on_done,
        )

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

        try:
            with GHLClient(get_token(), get_location_id()) as client:
                users = users_svc.list_users(client)
        except Exception as e:
            self.notify(f"Could not load users: {e}", severity="error")
            users = []
        self.app.push_screen(
            ContactEditModal(
                contact=detail.contact,
                custom_field_defs=detail.custom_field_defs,
                custom_values_map=detail.custom_values_map,
                custom_value_id_map=detail.custom_value_id_map,
                users=users or [],
            ),
            on_done,
        )

    def action_add_tag(self) -> None:
        detail = self.query_one("#contact-detail", ContactDetail)
        if not detail.contact_id:
            self.notify("Select a contact first", severity="warning")
            return
        cid = detail.contact_id

        def on_done(_: object) -> None:
            self.load_contact_detail(cid)
        self.app.push_screen(AddTagModal(cid), on_done)

    def action_remove_tag(self) -> None:
        detail = self.query_one("#contact-detail", ContactDetail)
        if not detail.contact_id or not (detail.contact and (detail.contact.get("tags"))):
            self.notify("Select a contact with tags first", severity="warning")
            return
        cid = detail.contact_id
        tags = detail.contact.get("tags", [])

        def on_done(_: object) -> None:
            self.load_contact_detail(cid)
        self.app.push_screen(RemoveTagModal(cid, tags), on_done)

    def action_notes(self) -> None:
        detail = self.query_one("#contact-detail", ContactDetail)
        if not detail.contact_id:
            self.notify("Select a contact first", severity="warning")
            return
        cid = detail.contact_id
        contact_name = _contact_label(detail.contact) if detail.contact else None

        def on_done(_: object) -> None:
            self.load_contact_detail(cid)
        self.app.push_screen(ContactNotesModal(cid, contact_name=contact_name), on_done)

    def action_tasks(self) -> None:
        detail = self.query_one("#contact-detail", ContactDetail)
        if not detail.contact_id:
            self.notify("Select a contact first", severity="warning")
            return
        cid = detail.contact_id
        contact_name = _contact_label(detail.contact) if detail.contact else None

        def on_done(_: object) -> None:
            self.load_contact_detail(cid)
        self.app.push_screen(ContactTasksModal(cid, contact_name=contact_name), on_done)

    def action_opportunities(self) -> None:
        detail = self.query_one("#contact-detail", ContactDetail)
        if not detail.contact_id:
            self.notify("Select a contact first", severity="warning")
            return
        cid = detail.contact_id

        def on_done(_: object) -> None:
            self.load_contact_detail(cid)
        self.app.push_screen(ContactOpportunitiesModal(cid), on_done)
