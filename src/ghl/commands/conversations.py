"""Conversation and messaging commands."""

from typing import Optional

import click

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..config import config_manager
from ..output import output_data, print_success

CONVERSATION_COLUMNS = [
    ("id", "ID"),
    ("contactId", "Contact ID"),
    ("type", "Type"),
    ("unreadCount", "Unread"),
    ("dateUpdated", "Last Updated"),
]

MESSAGE_COLUMNS = [
    ("id", "ID"),
    ("type", "Type"),
    ("direction", "Direction"),
    ("body", "Message"),
    ("dateAdded", "Sent"),
]


@click.group()
def conversations():
    """Manage conversations and messages."""
    pass


@conversations.command("list")
@click.option("--contact", "-c", "contact_id", help="Filter by contact ID")
@click.option("--limit", "-l", default=20, help="Number of results")
@click.pass_context
def list_conversations(ctx, contact_id: Optional[str], limit: int):
    """List conversations."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        params = {"limit": limit}
        if contact_id:
            params["contactId"] = contact_id

        response = client.get("/conversations/search", params=params)
        conversations_list = response.get("conversations", [])

        output_data(
            conversations_list,
            columns=CONVERSATION_COLUMNS,
            format=output_format,
            title="Conversations",
        )


@conversations.command("get")
@click.argument("conversation_id")
@click.pass_context
def get_conversation(ctx, conversation_id: str):
    """Get conversation details."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.get(f"/conversations/{conversation_id}")
        conversation = response.get("conversation", response)

        fields = [
            ("id", "ID"),
            ("contactId", "Contact ID"),
            ("type", "Type"),
            ("unreadCount", "Unread Messages"),
            ("dateAdded", "Created"),
            ("dateUpdated", "Last Updated"),
        ]

        output_data(conversation, format=output_format, single_fields=fields)


@conversations.command("messages")
@click.argument("conversation_id")
@click.option("--limit", "-l", default=20, help="Number of messages")
@click.pass_context
def list_messages(ctx, conversation_id: str, limit: int):
    """List messages in a conversation."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.get(
            f"/conversations/{conversation_id}/messages", params={"limit": limit}
        )
        messages = response.get("messages", [])

        output_data(
            messages,
            columns=MESSAGE_COLUMNS,
            format=output_format,
            title=f"Messages in Conversation {conversation_id}",
        )


@conversations.command("send")
@click.option("--contact", "-c", "contact_id", required=True, help="Contact ID")
@click.option(
    "--type",
    "-t",
    "message_type",
    required=True,
    type=click.Choice(["sms", "email", "whatsapp", "fb", "ig"]),
    help="Message type",
)
@click.option("--message", "-m", required=True, help="Message body")
@click.option("--subject", "-s", help="Email subject (required for email)")
@click.pass_context
def send_message(
    ctx,
    contact_id: str,
    message_type: str,
    message: str,
    subject: Optional[str],
):
    """Send a message to a contact."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    if message_type == "email" and not subject:
        raise click.ClickException("Email messages require --subject")

    with GHLClient(token, location_id) as client:
        data = {
            "contactId": contact_id,
            "type": message_type.upper() if message_type in ["sms", "email"] else message_type,
            "message": message,
        }

        if subject:
            data["subject"] = subject

        # Map message types to API format
        type_map = {
            "sms": "SMS",
            "email": "Email",
            "whatsapp": "WhatsApp",
            "fb": "FB",
            "ig": "IG",
        }
        data["type"] = type_map.get(message_type, message_type)

        response = client.post("/conversations/messages", json=data)
        msg = response.get("message", response)

        if output_format == "quiet":
            click.echo(msg.get("id") or msg.get("messageId"))
        else:
            print_success(f"Message sent: {msg.get('id') or msg.get('messageId')}")


@conversations.command("search")
@click.argument("query")
@click.option("--limit", "-l", default=20, help="Number of results")
@click.pass_context
def search_conversations(ctx, query: str, limit: int):
    """Search conversations."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.get("/conversations/search", params={"q": query, "limit": limit})
        conversations_list = response.get("conversations", [])

        output_data(
            conversations_list,
            columns=CONVERSATION_COLUMNS,
            format=output_format,
            title=f"Search Results for '{query}'",
        )


@conversations.command("create")
@click.option("--contact", "-c", "contact_id", required=True, help="Contact ID")
@click.pass_context
def create_conversation(ctx, contact_id: str):
    """Create a new conversation with a contact."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.post(
            "/conversations/",
            json={"contactId": contact_id, "locationId": location_id},
        )
        conversation = response.get("conversation", response)

        if output_format == "quiet":
            click.echo(conversation.get("id"))
        else:
            print_success(f"Conversation created: {conversation.get('id')}")
