"""Filter and saved-search modals for contacts."""

from __future__ import annotations

from typing import Any, Optional

from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static

from ..saved_searches import list_saved_searches, save_search


def _filter_dict(
    tags: list[str], assigned_to: Optional[str], query: Optional[str]
) -> dict[str, Any]:
    return {
        "tags": [t.strip() for t in tags if t.strip()],
        "assignedTo": (assigned_to or "").strip() or None,
        "query": (query or "").strip() or None,
    }


class ContactFilterModal(ModalScreen[Optional[dict[str, Any]]]):
    """Modal to set contact filters: tags, assigned user, query. Apply or Save as search."""

    def __init__(
        self,
        users: list[dict],
        current_filter: Optional[dict[str, Any]] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._users = users
        self._current = current_filter or {}

    def compose(self):
        # Select options: (display_label, value)
        opts: list[tuple[str, str]] = [("Any", "")]
        for u in self._users:
            uid = u.get("id") or ""
            label = u.get("name") or u.get("email") or uid or "—"
            opts.append((label[:50], uid))
        with Vertical():
            yield Label("Tags (comma-separated)")
            yield Input(
                value=", ".join(self._current.get("tags") or []),
                placeholder="tag1, tag2",
                id="filter-tags",
            )
            yield Label("Assigned to")
            yield Select(opts, value=self._current.get("assignedTo") or "", id="filter-assigned")
            yield Label("Text search (name, email, etc.)")
            yield Input(
                value=self._current.get("query") or "",
                placeholder="Search…",
                id="filter-query",
            )
            yield Label("Save as search name (optional)")
            yield Input(placeholder="My saved search", id="filter-save-name")
            yield Static("")
            with Vertical():
                yield Button("Apply", variant="primary", id="filter-apply")
                yield Button("Save as search", id="filter-save")
                yield Button("Clear filters", id="filter-clear")
                yield Button("Cancel", id="filter-cancel")

    def on_mount(self) -> None:
        self.query_one("#filter-tags", Input).focus()

    def _get_filter(self) -> dict[str, Any]:
        tags_in = self.query_one("#filter-tags", Input).value or ""
        tags = [t.strip() for t in tags_in.split(",") if t.strip()]
        assigned = self.query_one("#filter-assigned", Select).value
        if assigned is None:
            assigned = ""
        assigned = str(assigned).strip() or None
        query = (self.query_one("#filter-query", Input).value or "").strip() or None
        return _filter_dict(tags, assigned, query)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "filter-cancel":
            self.dismiss(None)
            return
        if event.button.id == "filter-clear":
            self.dismiss(_filter_dict([], None, None))
            return
        if event.button.id == "filter-apply":
            self.dismiss(self._get_filter())
            return
        if event.button.id == "filter-save":
            name_in = (self.query_one("#filter-save-name", Input).value or "").strip()
            if not name_in:
                self.notify("Enter a name for the saved search", severity="warning")
                return
            f = self._get_filter()
            save_search(
                name=name_in,
                tags=f.get("tags") or None,
                assigned_to=f.get("assignedTo"),
                query=f.get("query"),
            )
            self.notify(f"Saved search '{name_in}'")
            self.dismiss(f)


class SavedSearchesModal(ModalScreen[Optional[tuple[dict[str, Any], Optional[str]]]]):
    """Pick a saved search or 'All contacts'. Returns (filter_dict, saved_search_name or None)."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._searches = list_saved_searches()

    def compose(self):
        with Vertical():
            yield Label("Saved searches")
            yield Button("All contacts", variant="primary", id="saved-all")
            for s in self._searches:
                name = s.get("name") or "Unnamed"
                bid = f"saved-{s.get('id', '')}"
                yield Button(name, id=bid)
            yield Button("Cancel", id="saved-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "saved-cancel":
            self.dismiss(None)
            return
        if bid == "saved-all":
            self.dismiss((_filter_dict([], None, None), None))
            return
        if bid is not None and bid.startswith("saved-"):
            sid = bid.replace("saved-", "", 1)
            for s in self._searches:
                if s.get("id") == sid:
                    self.dismiss(
                        (
                            _filter_dict(
                                s.get("tags") or [],
                                s.get("assignedTo"),
                                s.get("query"),
                            ),
                            s.get("name"),
                        )
                    )
                    return
            self.dismiss(None)
