"""Opportunity detail modal (read-only)."""

from __future__ import annotations

from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..services.opportunities import get_opportunity


class OpportunityDetailModal(ModalScreen[None]):
    """Show opportunity details."""

    def __init__(self, opportunity_id: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._opportunity_id = opportunity_id

    def compose(self):
        with Vertical():
            yield Static("Loading…", id="opp-detail")
            yield Button("Close", id="opp-close")

    def on_mount(self) -> None:
        with GHLClient(get_token(), get_location_id()) as client:
            opp = get_opportunity(client, self._opportunity_id)
        lines = [
            f"[bold]{opp.get('name') or '—'}[/bold]",
            f"Value: {opp.get('monetaryValue')}",
            f"Status: {opp.get('status')}",
            f"Contact: {(opp.get('contact') or {}).get('name') or (opp.get('contact') or {}).get('email') or '—'}",
            f"Stage ID: {opp.get('pipelineStageId')}",
        ]
        self.query_one("#opp-detail", Static).update("\n".join(lines))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "opp-close":
            self.dismiss(None)
