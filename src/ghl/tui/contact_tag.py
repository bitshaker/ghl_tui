"""Add/remove tag modals."""

from __future__ import annotations

from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListView, ListItem

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..services import contacts as contact_svc


class AddTagModal(ModalScreen[None]):
    """Modal to add a tag to the current contact."""

    def __init__(self, contact_id: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._contact_id = contact_id

    def compose(self):
        with Vertical():
            yield Label("Tag name")
            yield Input(placeholder="Tag…", id="tag-input")
            yield Button("Add", variant="primary", id="tag-add")
            yield Button("Cancel", id="tag-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "tag-cancel":
            self.dismiss(None)
        elif event.button.id == "tag-add":
            inp = self.query_one("#tag-input", Input)
            tag = inp.value.strip()
            if tag:
                with GHLClient(get_token(), get_location_id()) as client:
                    contact_svc.add_tag(client, self._contact_id, [tag])
                self.app.notify(f"Tag '{tag}' added")
            self.dismiss(None)


class RemoveTagModal(ModalScreen[None]):
    """Modal to remove a tag from the current contact."""

    def __init__(self, contact_id: str, tags: list[str], **kwargs) -> None:
        super().__init__(**kwargs)
        self._contact_id = contact_id
        self._tags = list(tags)

    def compose(self):
        with Vertical():
            yield Label("Select tag to remove")
            list_view = ListView(id="tag-list")
            for t in self._tags:
                list_view.append(ListItem(Label(t)))
            yield list_view
            yield Button("Remove selected", variant="primary", id="tag-remove")
            yield Button("Cancel", id="tag-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "tag-cancel":
            self.dismiss(None)
        elif event.button.id == "tag-remove":
            lst = self.query_one("#tag-list", ListView)
            idx = lst.index
            if 0 <= idx < len(self._tags):
                tag = self._tags[idx]
                with GHLClient(get_token(), get_location_id()) as client:
                    contact_svc.remove_tag(client, self._contact_id, [tag])
                self.app.notify(f"Tag '{tag}' removed")
            self.dismiss(None)
