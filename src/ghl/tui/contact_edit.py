"""Create/edit contact modal."""

from __future__ import annotations

from typing import Optional

from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..services import contacts as contact_svc
from ..services import custom_fields as custom_fields_svc


class ContactEditModal(ModalScreen[dict]):
    """Modal to create or edit a contact."""

    def __init__(
        self,
        contact: Optional[dict] = None,
        *,
        custom_field_defs: Optional[list[dict]] = None,
        custom_values_map: Optional[dict[str, str]] = None,
        custom_value_id_map: Optional[dict[str, str]] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._contact = contact
        self._is_edit = contact is not None
        self._custom_field_defs = custom_field_defs or []
        self._custom_values_map = custom_values_map or {}
        self._custom_value_id_map = custom_value_id_map or {}
        self._custom_field_ids: list[str] = []  # fid for each custom field, in order
        self._dropdown_field_ids: set[str] = set()  # fields rendered as Select

    def _safe_id(self, fid: str) -> str:
        return "custom-" + "".join(c if c.isalnum() or c in "-_" else "_" for c in fid)

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
            self._custom_field_ids = []
            self._dropdown_field_ids = set()
            for field in self._custom_field_defs:
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
                    # Ensure current value is in options (in case it was removed or options use different format)
                    if value and not any(v == value for (_, v) in options):
                        options.append((value, value))
                    yield Label(name)
                    yield Select(options, value=value or "", allow_blank=True, id=self._safe_id(fid))
                else:
                    yield Label(name)
                    yield Input(value=value, placeholder=name, id=self._safe_id(fid))
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
                    custom_fields=custom_fields_payload if custom_fields_payload else None,
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
