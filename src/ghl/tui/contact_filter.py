"""Filter and saved-search modals for contacts."""

from __future__ import annotations

from typing import Any, Optional

from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static

from ..saved_searches import list_saved_searches, save_search
from ..services import custom_fields as custom_fields_svc

# Operators supported for custom field filters (subset of API)
CF_OPERATORS = [
    ("Equals", "eq"),
    ("Not equals", "not_eq"),
    ("Contains", "contains"),
    ("Not contains", "not_contains"),
    ("Exists", "exists"),
    ("Not exists", "not_exists"),
]


def _filter_dict(
    tags: list[str],
    assigned_to: Optional[str],
    query: Optional[str],
    custom_field_filters: Optional[list[dict]] = None,
) -> dict[str, Any]:
    return {
        "tags": [t.strip() for t in tags if t.strip()],
        "assignedTo": (assigned_to or "").strip() or None,
        "query": (query or "").strip() or None,
        "customFieldFilters": list(custom_field_filters) if custom_field_filters else [],
    }


class ContactFilterModal(ModalScreen[Optional[dict[str, Any]]]):
    """Modal to set contact filters: tags, assigned user, query, custom fields. Apply or Save as search."""

    def __init__(
        self,
        users: list[dict],
        custom_field_defs: Optional[list[dict]] = None,
        current_filter: Optional[dict[str, Any]] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._users = users
        self._custom_field_defs = custom_field_defs or []
        self._current = current_filter or {}
        self._cf_row_counter = 0
        self._cf_value_widget_counter = 0

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
            yield Label("Custom field filters")
            yield Vertical(id="custom-filters-container")
            yield Button("Add custom field filter", id="filter-add-cf")
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
        self._refresh_custom_filter_rows()

    def _cf_field_options(self) -> list[tuple[str, str]]:
        """Options for custom field Select: (display name, field_id)."""
        options: list[tuple[str, str]] = [("— Select field —", "")]
        for f in self._custom_field_defs:
            fid = str(f.get("id") or f.get("customFieldId", ""))
            if not fid:
                continue
            name = f.get("name") or f.get("label") or fid
            options.append((str(name)[:40], fid))
        return options

    def _get_field_def(self, field_id: str) -> Optional[dict]:
        """Return the custom field definition for the given field_id."""
        if not field_id:
            return None
        for f in self._custom_field_defs:
            fid = str(f.get("id") or f.get("customFieldId", ""))
            if fid == field_id:
                return f
        return None

    def _make_value_widget(
        self,
        row_id: str,
        field_id: str,
        value: str,
        for_dropdown: bool,
        options: list[tuple[str, str]],
        id_suffix: Optional[str] = None,
    ):
        """Create either an Input or a Select for the value cell based on field type.
        id_suffix: if set, appended to id to avoid duplicates when swapping widgets.
        """
        suf = f"-{id_suffix}" if id_suffix else ""
        if for_dropdown and options:
            opts = [("— Any —", "")] + options
            w = Select(opts, value=value if value else "", id=f"{row_id}-value-select{suf}")
            w.styles.min_width = 8
            w.styles.max_width = 24
        else:
            w = Input(
                value=value,
                placeholder="Value (leave empty for exists/not exists)",
                id=f"{row_id}-value-input{suf}",
            )
            w.styles.min_width = 8
            w.styles.max_width = 24
        return w

    def _make_cf_row(
        self,
        field_id: str = "",
        operator: str = "eq",
        value: str = "",
    ) -> Horizontal:
        """Build one custom filter row. Value is Input or Select (dropdown) based on field."""
        self._cf_row_counter += 1
        row_id = f"cf-row-{self._cf_row_counter}"
        field_opts = self._cf_field_options()
        op_opts = CF_OPERATORS
        field_select = Select(field_opts, value=field_id or "", id=f"{row_id}-field")
        op_select = Select(op_opts, value=operator, id=f"{row_id}-op")
        # Value: dropdown of options if field has options, else text input
        field_def = self._get_field_def(field_id) if field_id else None
        has_options = field_def is not None and custom_fields_svc.field_has_options(field_def)
        options = custom_fields_svc.get_field_options(field_def) if field_def else []
        value_widget = self._make_value_widget(row_id, field_id, value, has_options, options)
        value_container = Vertical(value_widget, classes="cf-value-cell", id=f"{row_id}-value-cell")
        remove_btn = Button("Remove", id=f"{row_id}-remove")
        # Prevent stretching; keep Selects and Button visible
        field_select.styles.min_width = 18
        field_select.styles.width = 22
        op_select.styles.min_width = 14
        op_select.styles.width = 18
        value_container.styles.min_width = 8
        value_container.styles.max_width = 24
        remove_btn.styles.width = 8
        row = Horizontal(*[field_select, op_select, value_container, remove_btn], classes="cf-row")
        return row

    def _refresh_custom_filter_rows(self) -> None:
        """Populate custom-filters-container from current_filter customFieldFilters."""
        container = self.query_one("#custom-filters-container", Vertical)
        container.remove_children()
        for cf in self._current.get("customFieldFilters") or []:
            row = self._make_cf_row(
                field_id=cf.get("field_id", ""),
                operator=cf.get("operator", "eq"),
                value=cf.get("value") or "",
            )
            container.mount(row)

    def _gather_custom_filter_rows(self) -> list[dict]:
        """Read custom field filter rows from the DOM."""
        result: list[dict] = []
        try:
            container = self.query_one("#custom-filters-container", Vertical)
        except Exception:
            return result
        for row in container.query("Horizontal.cf-row"):
            selects = row.query(Select)
            if len(selects) < 2:
                continue
            field_id = (selects[0].value or "").strip()
            if not field_id:
                continue
            operator = (selects[1].value or "eq").strip()
            value = ""
            value_cell = row.query_one(".cf-value-cell")
            if value_cell and value_cell.children:
                first = value_cell.children[0]
                value = (first.value or "").strip() if hasattr(first, "value") else ""
            if operator in ("exists", "not_exists"):
                value = ""
            result.append({"field_id": field_id, "operator": operator, "value": value})
        return result

    def _get_filter(self) -> dict[str, Any]:
        tags_in = self.query_one("#filter-tags", Input).value or ""
        tags = [t.strip() for t in tags_in.split(",") if t.strip()]
        assigned = self.query_one("#filter-assigned", Select).value
        if assigned is None:
            assigned = ""
        assigned = str(assigned).strip() or None
        query = (self.query_one("#filter-query", Input).value or "").strip() or None
        custom_filters = self._gather_custom_filter_rows()
        return _filter_dict(tags, assigned, query, custom_filters)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "filter-cancel":
            self.dismiss(None)
            return
        if event.button.id == "filter-clear":
            self.dismiss(_filter_dict([], None, None, []))
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
                custom_field_filters=f.get("customFieldFilters") or None,
            )
            self.notify(f"Saved search '{name_in}'")
            self.dismiss(f)
            return
        if event.button.id == "filter-add-cf":
            container = self.query_one("#custom-filters-container", Vertical)
            first_id = ""
            if self._custom_field_defs:
                f = self._custom_field_defs[0]
                first_id = str(f.get("id") or f.get("customFieldId", ""))
            row = self._make_cf_row(field_id=first_id, operator="eq", value="")
            container.mount(row)
            return
        if event.button.id and event.button.id.endswith("-remove"):
            parent = event.button.parent
            if parent is not None:
                parent.remove()
            return

    def _on_cf_field_changed(self, row_id: str, value_cell: Vertical, new_field_id: str) -> None:
        """Swap value widget to Input or Select when the field selection changes."""
        current_value = ""
        if value_cell.children:
            first = value_cell.children[0]
            if hasattr(first, "value"):
                current_value = (first.value or "").strip()
        value_cell.remove_children()
        self._cf_value_widget_counter += 1
        id_suffix = str(self._cf_value_widget_counter)
        field_def = self._get_field_def(new_field_id) if new_field_id else None
        has_options = field_def is not None and custom_fields_svc.field_has_options(field_def)
        options = custom_fields_svc.get_field_options(field_def) if field_def else []
        value_widget = self._make_value_widget(
            row_id, new_field_id, current_value, has_options, options, id_suffix=id_suffix
        )
        value_cell.mount(value_widget)

    def on_select_changed(self, event: Select.Changed) -> None:
        """When the custom field dropdown changes, swap value widget to Input or options Select."""
        if not event.control.id or not event.control.id.endswith("-field"):
            return
        row_id = event.control.id.replace("-field", "")
        row = event.control.parent
        if not row or not hasattr(row, "query_one"):
            return
        try:
            value_cell = row.query_one(".cf-value-cell")
        except Exception:
            return
        new_field_id = (event.value or "").strip()
        # Skip if this is the initial value (no user change); avoids duplicate-id when row first mounts
        if not new_field_id:
            return
        self._on_cf_field_changed(row_id, value_cell, new_field_id)


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
            self.dismiss((_filter_dict([], None, None, []), None))
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
                                s.get("customFieldFilters") or [],
                            ),
                            s.get("name"),
                        )
                    )
                    return
            self.dismiss(None)
