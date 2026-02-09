"""Create/edit contact modal."""

from __future__ import annotations

from typing import Optional

from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..services import contacts as contact_svc


class ContactEditModal(ModalScreen[dict]):
    """Modal to create or edit a contact."""

    def __init__(self, contact: Optional[dict] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._contact = contact
        self._is_edit = contact is not None

    def compose(self):
        with Vertical():
            yield Label("Email" if self._is_edit else "Email *")
            yield Input(
                value=(self._contact or {}).get("email", ""),
                placeholder="email@example.com",
                id="contact-email",
            )
            yield Label("Phone")
            yield Input(
                value=(self._contact or {}).get("phone", ""),
                placeholder="+1…",
                id="contact-phone",
            )
            yield Label("First name")
            yield Input(
                value=(self._contact or {}).get("firstName", ""),
                placeholder="First",
                id="contact-first",
            )
            yield Label("Last name")
            yield Input(
                value=(self._contact or {}).get("lastName", ""),
                placeholder="Last",
                id="contact-last",
            )
            yield Label("Company")
            yield Input(
                value=(self._contact or {}).get("companyName", ""),
                placeholder="Company",
                id="contact-company",
            )
            yield Label("Source")
            yield Input(
                value=(self._contact or {}).get("source", ""),
                placeholder="Lead source",
                id="contact-source",
            )
            with Vertical():
                yield Button("Save", variant="primary", id="contact-save")
                yield Button("Cancel", id="contact-cancel")

    def on_mount(self) -> None:
        self.query_one("#contact-email", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "contact-cancel":
            self.dismiss(None)
            return
        if event.button.id == "contact-save":
            self._save()

    def _save(self) -> None:
        email = self.query_one("#contact-email", Input).value.strip() or None
        phone = self.query_one("#contact-phone", Input).value.strip() or None
        first = self.query_one("#contact-first", Input).value.strip() or None
        last = self.query_one("#contact-last", Input).value.strip() or None
        company = self.query_one("#contact-company", Input).value.strip() or None
        source = self.query_one("#contact-source", Input).value.strip() or None
        if not self._is_edit and not email and not phone:
            self.notify("Email or phone required", severity="error")
            return
        location_id = get_location_id()
        with GHLClient(get_token(), location_id) as client:
            if self._is_edit and self._contact:
                contact_svc.update_contact(
                    client,
                    self._contact["id"],
                    email=email,
                    phone=phone,
                    first_name=first,
                    last_name=last,
                    company_name=company,
                    source=source,
                )
                updated = contact_svc.get_contact(client, self._contact["id"])
                self.dismiss(updated)
            else:
                created = contact_svc.create_contact(
                    client,
                    location_id=location_id,
                    email=email,
                    phone=phone,
                    first_name=first,
                    last_name=last,
                    company_name=company,
                    source=source,
                )
                self.dismiss(created)
        self.app.notify("Contact saved")
