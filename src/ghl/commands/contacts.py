"""Contact management commands."""

from typing import Optional

import click

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..config import config_manager
from ..output import output_data, print_success

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
def contacts():
    """Manage contacts."""
    pass


@contacts.command("list")
@click.option("--limit", "-l", default=20, help="Number of contacts to return")
@click.option("--query", "-q", help="Search query")
@click.pass_context
def list_contacts(ctx, limit: int, query: Optional[str]):
    """List contacts in the location."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        params = {"limit": limit}
        if query:
            params["query"] = query

        response = client.get("/contacts/", params=params)
        contacts_list = response.get("contacts", [])

        output_data(
            contacts_list,
            columns=CONTACT_COLUMNS,
            format=output_format,
            title=f"Contacts ({len(contacts_list)})",
        )


@contacts.command("get")
@click.argument("contact_id")
@click.pass_context
def get_contact(ctx, contact_id: str):
    """Get a contact by ID."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.get(f"/contacts/{contact_id}")
        contact = response.get("contact", response)

        output_data(
            contact,
            format=output_format,
            single_fields=CONTACT_FIELDS,
        )


@contacts.command("create")
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
        data = {"locationId": location_id}

        if email:
            data["email"] = email
        if phone:
            data["phone"] = phone
        if first_name:
            data["firstName"] = first_name
        if last_name:
            data["lastName"] = last_name
        if name:
            data["name"] = name
        if company:
            data["companyName"] = company
        if source:
            data["source"] = source
        if tag:
            data["tags"] = list(tag)

        response = client.post("/contacts/", json=data)
        contact = response.get("contact", response)

        if output_format == "quiet":
            click.echo(contact.get("id"))
        else:
            print_success(f"Contact created: {contact.get('id')}")
            output_data(contact, format=output_format, single_fields=CONTACT_FIELDS)


@contacts.command("update")
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

    with GHLClient(token, location_id) as client:
        data = {}

        if email:
            data["email"] = email
        if phone:
            data["phone"] = phone
        if first_name:
            data["firstName"] = first_name
        if last_name:
            data["lastName"] = last_name
        if company:
            data["companyName"] = company
        if source:
            data["source"] = source

        if not data:
            raise click.ClickException("No fields to update. Specify at least one option.")

        response = client.put(f"/contacts/{contact_id}", json=data)
        contact = response.get("contact", response)

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
        client.delete(f"/contacts/{contact_id}")
        print_success(f"Contact deleted: {contact_id}")


@contacts.command("search")
@click.argument("query")
@click.option("--limit", "-l", default=20, help="Number of results")
@click.pass_context
def search_contacts(ctx, query: str, limit: int):
    """Search for contacts by name, email, or phone."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.get("/contacts/", params={"query": query, "limit": limit})
        contacts_list = response.get("contacts", [])

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
        # First get existing tags
        response = client.get(f"/contacts/{contact_id}")
        contact = response.get("contact", response)
        existing_tags = contact.get("tags", []) or []

        # Add new tags
        all_tags = list(set(existing_tags + list(tag)))

        # Update contact
        client.put(f"/contacts/{contact_id}", json={"tags": all_tags})
        print_success(f"Tags added to contact: {', '.join(tag)}")


@contacts.command("untag")
@click.argument("contact_id")
@click.option("--tag", "-t", required=True, multiple=True, help="Tag to remove")
def remove_tag(contact_id: str, tag: tuple):
    """Remove tags from a contact."""
    token = get_token()
    location_id = get_location_id()

    with GHLClient(token, location_id) as client:
        # First get existing tags
        response = client.get(f"/contacts/{contact_id}")
        contact = response.get("contact", response)
        existing_tags = contact.get("tags", []) or []

        # Remove specified tags
        new_tags = [t for t in existing_tags if t not in tag]

        # Update contact
        client.put(f"/contacts/{contact_id}", json={"tags": new_tags})
        print_success(f"Tags removed from contact: {', '.join(tag)}")


@contacts.command("tasks")
@click.argument("contact_id")
@click.pass_context
def list_tasks(ctx, contact_id: str):
    """List tasks for a contact."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.get(f"/contacts/{contact_id}/tasks")
        tasks = response.get("tasks", [])

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


@contacts.command("notes")
@click.argument("contact_id")
@click.pass_context
def list_notes(ctx, contact_id: str):
    """List notes for a contact."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.get(f"/contacts/{contact_id}/notes")
        notes = response.get("notes", [])

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
        response = client.post(f"/contacts/{contact_id}/notes", json={"body": note})
        note_id = response.get("note", {}).get("id") or response.get("id")
        print_success(f"Note added: {note_id}")
