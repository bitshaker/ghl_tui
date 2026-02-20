"""Modal listing opportunities for a contact."""

from __future__ import annotations

from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, ListItem, ListView, Static

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..services.opportunities import list_opportunities


class ContactOpportunitiesModal(ModalScreen[None]):
    """Show opportunities for the current contact."""

    CSS = """
    #opps-buttons Button {
        margin-right: 2;
    }
    """

    def __init__(self, contact_id: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._contact_id = contact_id

    def compose(self):
        with Vertical():
            yield Label("Opportunities for this contact")
            yield ListView(id="contact-opps-list")
            yield Static("", id="contact-opps-empty")
            with Horizontal(id="opps-buttons"):
                yield Button("Close", id="opps-close")

    def on_mount(self) -> None:
        with GHLClient(get_token(), get_location_id()) as client:
            opps = list_opportunities(client, contact_id=self._contact_id, limit=50)
        lst = self.query_one("#contact-opps-list", ListView)
        empty = self.query_one("#contact-opps-empty", Static)
        if not opps:
            empty.update("No opportunities found.")
        else:
            for o in opps:
                name = o.get("name") or "—"
                val = o.get("monetaryValue")
                val_s = f" ${val:,.0f}" if val is not None else ""
                lst.append(ListItem(Label(f"  {name}{val_s}  [{o.get('status')}]")))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "opps-close":
            self.dismiss(None)
