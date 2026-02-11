"""Custom fields CLI - list field definitions and inspect raw API response for debugging."""

import click

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..config import config_manager
from ..options import output_format_options
from ..output import output_data, output_json
from ..services import custom_fields as custom_fields_svc


@click.group("custom-fields")
@output_format_options
def custom_fields():
    """List and inspect custom field definitions (for debugging dropdown options, etc.)."""
    pass


@custom_fields.command("list")
@output_format_options
@click.option(
    "--raw",
    is_flag=True,
    help="Dump raw API response as JSON (for debugging option structure).",
)
@click.pass_context
def list_custom_fields_cmd(ctx, raw: bool):
    """List custom fields for the current location.

    Use --json to see full field objects. Use --raw to see the exact API
    response (helps debug dropdown options parsing).
    """
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        path = f"/locations/{location_id}/customFields"
        response = client.get(path, include_location_id=False)

    if raw:
        output_json(response)
        return

    fields = response.get("customFields", response.get("fields", []))
    if not isinstance(fields, list):
        fields = []

    # Filter to contact-scoped for consistency with TUI
    fields = [
        f for f in fields
        if f.get("entityType", "contact") == "contact" or "entityType" not in f
    ]

    if output_format == "json":
        output_json(fields)
        return

    if output_format == "quiet":
        for f in fields:
            click.echo(f.get("id") or f.get("customFieldId") or "")
        return

    # Table: name, id, type, has options
    columns = [
        ("name", "Name"),
        ("id", "ID"),
        ("fieldType", "Type"),
        ("_options_preview", "Options"),
    ]
    rows = []
    for f in fields:
        name = f.get("name") or f.get("label") or "—"
        fid = f.get("id") or f.get("customFieldId") or "—"
        ftype = f.get("fieldType") or f.get("type") or "—"
        opts = custom_fields_svc.get_field_options(f)
        if opts:
            preview = ", ".join(label for label, _ in opts[:3])
            if len(opts) > 3:
                preview += f" (+{len(opts) - 3} more)"
        else:
            preview = "(use --raw to see API structure)"
        rows.append({
            "name": name,
            "id": fid,
            "fieldType": ftype,
            "_options_preview": preview,
        })

    output_data(
        rows,
        columns=columns,
        format=output_format,
        title="Custom fields (contact)",
    )


@custom_fields.command("values")
@click.option("--contact", "contact_id", required=True, help="Contact ID to list custom values for.")
@click.option("--raw", is_flag=True, help="Dump raw API response as JSON.")
@click.pass_context
def list_custom_values_cmd(ctx, contact_id: str, raw: bool):
    """List custom values for a contact (for debugging)."""
    token = get_token()
    location_id = get_location_id()

    with GHLClient(token, location_id) as client:
        path = f"/locations/{location_id}/customValues"
        params = {"contactId": contact_id}
        response = client.get(path, params=params, include_location_id=False)

    if raw:
        output_json(response)
        return

    values = response.get("customValues", response.get("values", []))
    if not isinstance(values, list):
        values = []
    output_json(values)
