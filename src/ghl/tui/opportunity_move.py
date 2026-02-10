"""Move opportunity to another stage modal."""

from __future__ import annotations

from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, ListView, ListItem

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..services.opportunities import move_opportunity


class MoveStageModal(ModalScreen[None]):
    """Pick a target stage to move the opportunity."""

    def __init__(
        self,
        opportunity_id: str,
        stage_ids: list[str],
        stage_names: list[str],
        *,
        current_stage_id: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._opportunity_id = opportunity_id
        self._stage_ids = stage_ids
        self._stage_names = stage_names
        self._current_stage_id = current_stage_id
        self._options = [
            (sid, name) for sid, name in zip(stage_ids, stage_names) if sid != current_stage_id
        ]

    def compose(self):
        with Vertical():
            yield Label("Move to stage:")
            items = [ListItem(Label(f"  {name}")) for _sid, name in self._options]
            yield ListView(*items, id="move-stage-list")
            yield Button("Move", variant="primary", id="move-do")
            yield Button("Cancel", id="move-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "move-cancel":
            self.dismiss(None)
            return
        if event.button.id == "move-do":
            idx = self.query_one("#move-stage-list", ListView).index
            if 0 <= idx < len(self._options):
                stage_id, _ = self._options[idx]
                with GHLClient(get_token(), get_location_id()) as client:
                    move_opportunity(client, self._opportunity_id, stage_id)
                self.app.notify("Opportunity moved")
            self.dismiss(None)
