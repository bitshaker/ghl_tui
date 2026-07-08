"""Create/edit contact modal."""

from __future__ import annotations

from typing import Iterator, Optional

from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Select

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..services import contacts as contact_svc
from ..services import custom_fields as custom_fields_svc


class ContactEditModal(ModalScreen[dict]):
    """Modal to create or edit a contact."""

    BINDINGS = [
        Binding("escape", "dismiss", "Cancel", priority=True),
    ]

    DEFAULT_CSS = """
    ContactEditModal {
        align: center middle;
    }
    #contact-edit-form {
        width: 88;
        min-width: 56;
        max-width: 95%;
        height: auto;
        max-height: 90%;
        padding: 1 1;
        border: solid $primary;
        background: $surface;
    }
    #contact-edit-fields {
        height: auto;
        max-height: 32;
        margin-bottom: 0;
    }
    .field-row {
        height: auto;
        max-height: 4;
        margin-bottom: 0;
    }
    .field-cell {
        width: 1fr;
        height: auto;
        min-width: 0;
        margin-right: 1;
    }
    .field-cell Label {
        height: 1;
        margin-bottom: 0;
    }
    .field-cell Input,
    .field-cell Select {
        width: 100%;
        min-width: 28;
        height: 3;
    }
    #contact-edit-actions {
        height: auto;
        margin-top: 1;
    }
    #contact-edit-actions Button {
        margin-right: 2;
    }
    """

    def __init__(
        self,
        contact: Optional[dict] = None,
        *,
        custom_field_defs: Optional[list[dict]] = None,
        custom_values_map: Optional[dict[str, str]] = None,
        custom_value_id_map: Optional[dict[str, str]] = None,
        users: Optional[list[dict]] = None,
        contact_type_options: Optional[list[tuple[str, str]]] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._contact = contact
        self._is_edit = contact is not None
        self._custom_field_defs = custom_field_defs or []
        self._custom_values_map = custom_values_map or {}
        self._custom_value_id_map = custom_value_id_map or {}
        self._users = users or []
        self._contact_type_options = contact_type_options or []
        self._custom_field_ids: list[str] = []  # fid for each custom field, in order
        self._dropdown_field_ids: set[str] = set()  # fields rendered as Select

    def _safe_id(self, fid: str) -> str:
        return "custom-" + "".join(c if c.isalnum() or c in "-_" else "_" for c in fid)

    def _field_cell(self, label: str, widget: Widget) -> Iterator[Widget]:
        with Vertical(classes="field-cell"):
            yield Label(label)
            yield widget

    def _field_row(
        self,
        left_label: str,
        left_widget: Widget,
        right_label: str | None = None,
        right_widget: Widget | None = None,
    ) -> Iterator[Widget]:
        with Horizontal(classes="field-row"):
            yield from self._field_cell(left_label, left_widget)
            if right_label is not None and right_widget is not None:
                yield from self._field_cell(right_label, right_widget)
            else:
                yield Vertical(classes="field-cell")

    def compose(self):
        with Vertical(id="contact-edit-form"):
            with ScrollableContainer(id="contact-edit-fields"):
                yield from self._field_row(
                    "First name",
                    Input(
                        value=(self._contact or {}).get("firstName", ""),
                        placeholder="First",
                        id="contact-first",
                    ),
                    "Last name",
                    Input(
                        value=(self._contact or {}).get("lastName", ""),
                        placeholder="Last",
                        id="contact-last",
                    ),
                )
                yield from self._field_row(
                    "Email" if self._is_edit else "Email *",
                    Input(
                        value=(self._contact or {}).get("email", ""),
                        placeholder="email@example.com",
                        id="contact-email",
                    ),
                    "Phone",
                    Input(
                        value=(self._contact or {}).get("phone", ""),
                        placeholder="+1…",
                        id="contact-phone",
                    ),
                )
                cur_ctype = (self._contact or {}).get("type") or ""
                if isinstance(cur_ctype, str):
                    cur_ctype = cur_ctype.strip()
                else:
                    cur_ctype = str(cur_ctype).strip() if cur_ctype is not None else ""
                ctype_opts: list[tuple[str, str]] = [("— (none)", "")]
                ctype_opts.extend(self._contact_type_options)
                if cur_ctype and not any(v == cur_ctype for (_, v) in ctype_opts):
                    ctype_opts.append((cur_ctype, cur_ctype))
                assigned_opts: list[tuple[str, str]] = [("— (unassigned)", "")]
                for u in self._users:
                    uid = u.get("id") or ""
                    label = u.get("name") or u.get("email") or uid or "—"
                    assigned_opts.append((label[:50], uid))
                current_assigned = (self._contact or {}).get("assignedTo") or ""
                if current_assigned and not any(v == current_assigned for (_, v) in assigned_opts):
                    assigned_opts.append((current_assigned, current_assigned))
                yield from self._field_row(
                    "Contact type",
                    Select(
                        ctype_opts,
                        value=cur_ctype or "",
                        allow_blank=True,
                        id="contact-type",
                    ),
                    "Assigned to",
                    Select(
                        assigned_opts,
                        value=current_assigned or "",
                        allow_blank=True,
                        id="contact-assigned",
                    ),
                )
                yield from self._field_row(
                    "Company",
                    Input(
                        value=(self._contact or {}).get("companyName", ""),
                        placeholder="Company",
                        id="contact-company",
                    ),
                    "Source",
                    Input(
                        value=(self._contact or {}).get("source", ""),
                        placeholder="Lead source",
                        id="contact-source",
                    ),
                )
                self._custom_field_ids = []
                self._dropdown_field_ids = set()
                custom_cells: list[tuple[str, Widget]] = []
                for field in self._custom_field_defs:
                    fk = (field.get("fieldKey") or field.get("key") or "").strip().lower()
                    if fk == "contact.type":
                        continue
                    fid = str(field.get("id") or field.get("customFieldId", ""))
                    if not fid:
                        continue
                    self._custom_field_ids.append(fid)
                    name = field.get("name") or field.get("label", fid)
                    value = self._custom_values_map.get(fid, "")
                    opts = custom_fields_svc.get_field_options(field)
                    is_dropdown = custom_fields_svc.field_has_options(field)
                    if is_dropdown:
                        self._dropdown_field_ids.add(fid)
                        options: list[tuple[str, str]] = [("— (empty)", "")]
                        options.extend(opts)
                        if value and not any(v == value for (_, v) in options):
                            options.append((value, value))
                        custom_cells.append(
                            (
                                name,
                                Select(
                                    options,
                                    value=value or "",
                                    allow_blank=True,
                                    id=self._safe_id(fid),
                                ),
                            )
                        )
                    else:
                        custom_cells.append(
                            (
                                name,
                                Input(value=value, placeholder=name, id=self._safe_id(fid)),
                            )
                        )
                for i in range(0, len(custom_cells), 2):
                    left_label, left_widget = custom_cells[i]
                    if i + 1 < len(custom_cells):
                        right_label, right_widget = custom_cells[i + 1]
                        yield from self._field_row(left_label, left_widget, right_label, right_widget)
                    else:
                        yield from self._field_row(left_label, left_widget)
            with Horizontal(id="contact-edit-actions"):
                yield Button("Save", variant="primary", id="contact-save")
                yield Button("Cancel", id="contact-cancel")

    def on_mount(self) -> None:
        self.query_one("#contact-first", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "contact-cancel":
            self.dismiss(None)
            return
        if event.button.id == "contact-save":
            self._save()

    def _gather_custom_values(self) -> dict[str, str]:
        """Collect custom field values from inputs and selects."""
        result: dict[str, str] = {}
        for fid in self._custom_field_ids:
            try:
                sid = self._safe_id(fid)
                if fid in self._dropdown_field_ids:
                    sel = self.query_one(f"#{sid}", Select)
                    val = sel.value
                    result[fid] = str(val).strip() if val is not None else ""
                else:
                    inp = self.query_one(f"#{sid}", Input)
                    result[fid] = inp.value.strip()
            except Exception:
                pass
        return result

    def _save(self) -> None:
        email = self.query_one("#contact-email", Input).value.strip() or None
        phone = self.query_one("#contact-phone", Input).value.strip() or None
        first = self.query_one("#contact-first", Input).value.strip() or None
        last = self.query_one("#contact-last", Input).value.strip() or None
        company = self.query_one("#contact-company", Input).value.strip() or None
        source = self.query_one("#contact-source", Input).value.strip() or None
        assigned_sel = self.query_one("#contact-assigned", Select)
        assigned = (assigned_sel.value or "").strip() if assigned_sel.value is not None else ""
        assigned_to = assigned or None
        type_sel = self.query_one("#contact-type", Select)
        type_raw = (type_sel.value or "").strip() if type_sel.value is not None else ""
        contact_type = type_raw if type_raw else None
        if not self._is_edit and not email and not phone:
            self.notify("Email or phone required", severity="error")
            return
        location_id = get_location_id()
        with GHLClient(get_token(), location_id) as client:
            if self._is_edit and self._contact:
                custom_values = self._gather_custom_values()
                # Build customFields for Update Contact body (no separate scope needed)
                custom_fields_payload: list[dict] = []
                for field in self._custom_field_defs:
                    fid = str(field.get("id") or field.get("customFieldId", ""))
                    if not fid:
                        continue
                    key = field.get("fieldKey") or field.get("key") or fid
                    value = custom_values.get(fid, "")
                    custom_fields_payload.append({
                        "id": fid,
                        "key": key,
                        "field_value": value,
                    })
                contact_svc.update_contact(
                    client,
                    self._contact["id"],
                    email=email,
                    phone=phone,
                    first_name=first,
                    last_name=last,
                    company_name=company,
                    source=source,
                    assigned_to=assigned_to,
                    contact_type=contact_type,
                    custom_fields=custom_fields_payload if custom_fields_payload else None,
                )
                updated = contact_svc.get_contact(client, self._contact["id"])
                self.dismiss(updated)
            else:
                custom_values = self._gather_custom_values()
                custom_fields_payload = []
                for field in self._custom_field_defs:
                    fid = str(field.get("id") or field.get("customFieldId", ""))
                    if not fid:
                        continue
                    key = field.get("fieldKey") or field.get("key") or fid
                    value = custom_values.get(fid, "")
                    custom_fields_payload.append({
                        "id": fid,
                        "key": key,
                        "field_value": value,
                    })
                created = contact_svc.create_contact(
                    client,
                    location_id=location_id,
                    email=email,
                    phone=phone,
                    first_name=first,
                    last_name=last,
                    company_name=company,
                    source=source,
                    assigned_to=assigned_to,
                    contact_type=contact_type,
                    custom_fields=custom_fields_payload if custom_fields_payload else None,
                )
                self.dismiss(created)
        self.app.notify("Contact saved")
