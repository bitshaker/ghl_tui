"""Contact management commands."""

from typing import Optional

import click

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..config import config_manager
from ..options import output_format_options
from ..output import output_data, print_success
from ..saved_searches import list_saved_searches
from ..services import contacts as contact_svc

# Column definitions for contact list
CONTACT_COLUMNS = [
    ("id", "ID"),
    ("firstName", "First Name"),
    ("lastName", "Last Name"),
    ("email", "Email"),
    ("phone", "Phone"),
    ("tags", "Tags"),
]

CONTACT_FIELDS = [
    ("id", "ID"),
    ("firstName", "First Name"),
    ("lastName", "Last Name"),
    ("name", "Full Name"),
    ("email", "Email"),
    ("phone", "Phone"),
    ("companyName", "Company"),
    ("address1", "Address"),
    ("city", "City"),
    ("state", "State"),
    ("postalCode", "Postal Code"),
    ("country", "Country"),
    ("source", "Source"),
    ("tags", "Tags"),
    ("dateAdded", "Created"),
    ("dateUpdated", "Updated"),
]


@click.group()
@output_format_options
def contacts():
    """Manage contacts."""
    pass


@contacts.command("list")
@output_format_options
@click.option("--limit", "-l", default=20, help="Number of contacts to return")
@click.option("--query", "-q", help="Search query (name, email, etc.)")
@click.option("--tag", "-t", "tags", multiple=True, help="Filter by tag (contacts must have this tag); can repeat")
@click.option("--assigned-to", help="Filter by assigned user ID")
@click.pass_context
def list_contacts(ctx, limit: int, query: Optional[str], tags: tuple, assigned_to: Optional[str]):
    """List contacts in the location. Use --tag and --assigned-to for filtered search (Search API)."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        tag_list = list(tags) if tags else None
        if tag_list or assigned_to:
            contacts_list = contact_svc.contacts_search(
                client,
                location_id,
                page_limit=limit,
                query=query,
                tags=tag_list,
                assigned_to=assigned_to,
            )
        else:
            contacts_list = contact_svc.list_contacts(client, limit=limit, query=query)

        output_data(
            contacts_list,
            columns=CONTACT_COLUMNS,
            format=output_format,
            title=f"Contacts ({len(contacts_list)})",
        )


@contacts.command("get")
@output_format_options
@click.argument("contact_id")
@click.pass_context
def get_contact(ctx, contact_id: str):
    """Get a contact by ID."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        contact = contact_svc.get_contact(client, contact_id)

        output_data(
            contact,
            format=output_format,
            single_fields=CONTACT_FIELDS,
        )


@contacts.command("create")
@output_format_options
@click.option("--email", "-e", help="Email address")
@click.option("--phone", "-p", help="Phone number")
@click.option("--first-name", "-f", help="First name")
@click.option("--last-name", "-l", help="Last name")
@click.option("--name", "-n", help="Full name (used if first/last not provided)")
@click.option("--company", help="Company name")
@click.option("--source", help="Lead source")
@click.option("--tag", multiple=True, help="Tags to add (can be used multiple times)")
@click.pass_context
def create_contact(
    ctx,
    email: Optional[str],
    phone: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    name: Optional[str],
    company: Optional[str],
    source: Optional[str],
    tag: tuple,
):
    """Create a new contact."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    if not email and not phone:
        raise click.ClickException("At least --email or --phone is required")

    with GHLClient(token, location_id) as client:
        contact = contact_svc.create_contact(
            client,
            location_id=location_id,
            email=email,
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            name=name,
            company_name=company,
            source=source,
            tags=list(tag) if tag else None,
        )

        if output_format == "quiet":
            click.echo(contact.get("id"))
        else:
            print_success(f"Contact created: {contact.get('id')}")
            output_data(contact, format=output_format, single_fields=CONTACT_FIELDS)


@contacts.command("update")
@output_format_options
@click.argument("contact_id")
@click.option("--email", "-e", help="Email address")
@click.option("--phone", "-p", help="Phone number")
@click.option("--first-name", "-f", help="First name")
@click.option("--last-name", "-l", help="Last name")
@click.option("--company", help="Company name")
@click.option("--source", help="Lead source")
@click.pass_context
def update_contact(
    ctx,
    contact_id: str,
    email: Optional[str],
    phone: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    company: Optional[str],
    source: Optional[str],
):
    """Update an existing contact."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    if not any(v is not None for v in (email, phone, first_name, last_name, company, source)):
        raise click.ClickException("No fields to update. Specify at least one option.")

    with GHLClient(token, location_id) as client:
        contact = contact_svc.update_contact(
            client,
            contact_id,
            email=email,
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            company_name=company,
            source=source,
        )

        print_success(f"Contact updated: {contact_id}")
        output_data(contact, format=output_format, single_fields=CONTACT_FIELDS)


@contacts.command("delete")
@click.argument("contact_id")
@click.confirmation_option(prompt="Are you sure you want to delete this contact?")
def delete_contact(contact_id: str):
    """Delete a contact."""
    token = get_token()
    location_id = get_location_id()

    with GHLClient(token, location_id) as client:
        contact_svc.delete_contact(client, contact_id)
        print_success(f"Contact deleted: {contact_id}")


@contacts.command("search")
@output_format_options
@click.argument("query")
@click.option("--limit", "-l", default=20, help="Number of results")
@click.pass_context
def search_contacts(ctx, query: str, limit: int):
    """Search for contacts by name, email, or phone."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        contacts_list = contact_svc.search_contacts(client, query, limit=limit)

        output_data(
            contacts_list,
            columns=CONTACT_COLUMNS,
            format=output_format,
            title=f"Search Results for '{query}'",
        )


@contacts.command("tag")
@click.argument("contact_id")
@click.option("--tag", "-t", required=True, multiple=True, help="Tag to add")
def add_tag(contact_id: str, tag: tuple):
    """Add tags to a contact."""
    token = get_token()
    location_id = get_location_id()

    with GHLClient(token, location_id) as client:
        contact_svc.add_tag(client, contact_id, list(tag))
        print_success(f"Tags added to contact: {', '.join(tag)}")


@contacts.command("untag")
@click.argument("contact_id")
@click.option("--tag", "-t", required=True, multiple=True, help="Tag to remove")
def remove_tag(contact_id: str, tag: tuple):
    """Remove tags from a contact."""
    token = get_token()
    location_id = get_location_id()

    with GHLClient(token, location_id) as client:
        contact_svc.remove_tag(client, contact_id, list(tag))
        print_success(f"Tags removed from contact: {', '.join(tag)}")


@contacts.command("tasks")
@output_format_options
@click.argument("contact_id")
@click.pass_context
def list_tasks(ctx, contact_id: str):
    """List tasks for a contact."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        tasks = contact_svc.list_tasks(client, contact_id)

        columns = [
            ("id", "ID"),
            ("title", "Title"),
            ("dueDate", "Due Date"),
            ("completed", "Completed"),
            ("assignedTo", "Assigned To"),
        ]

        output_data(
            tasks,
            columns=columns,
            format=output_format,
            title=f"Tasks for Contact {contact_id}",
        )


@contacts.command("saved-searches")
@output_format_options
@click.pass_context
def list_saved_searches_cmd(ctx):
    """List locally saved contact search filters (tags, assigned user, query)."""
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format
    searches = list_saved_searches()
    if not searches:
        click.echo("No saved searches. Use the TUI (f = Filter, then Save as search) to create them.")
        return
    rows = [
        {
            "name": s.get("name", ""),
            "tags": ", ".join(s.get("tags") or []),
            "assignedTo": s.get("assignedTo") or "—",
            "query": s.get("query") or "—",
        }
        for s in searches
    ]
    output_data(
        rows,
        columns=[("name", "Name"), ("tags", "Tags"), ("assignedTo", "Assigned To"), ("query", "Query")],
        format=output_format,
        title="Saved searches",
    )


@contacts.command("notes")
@output_format_options
@click.argument("contact_id")
@click.pass_context
def list_notes(ctx, contact_id: str):
    """List notes for a contact."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        notes = contact_svc.list_notes(client, contact_id)

        columns = [
            ("id", "ID"),
            ("body", "Note"),
            ("dateAdded", "Created"),
        ]

        output_data(
            notes,
            columns=columns,
            format=output_format,
            title=f"Notes for Contact {contact_id}",
        )


@contacts.command("add-note")
@click.argument("contact_id")
@click.argument("note")
def add_note(contact_id: str, note: str):
    """Add a note to a contact."""
    token = get_token()
    location_id = get_location_id()

    with GHLClient(token, location_id) as client:
        result = contact_svc.add_note(client, contact_id, note)
        note_id = result.get("id") if isinstance(result, dict) else None
        print_success(f"Note added: {note_id or 'ok'}")
