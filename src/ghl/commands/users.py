"""User management commands."""

import click

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..config import config_manager
from ..output import output_data

USER_COLUMNS = [
    ("id", "ID"),
    ("name", "Name"),
    ("email", "Email"),
    ("role", "Role"),
    ("phone", "Phone"),
]

USER_FIELDS = [
    ("id", "ID"),
    ("name", "Name"),
    ("firstName", "First Name"),
    ("lastName", "Last Name"),
    ("email", "Email"),
    ("phone", "Phone"),
    ("extension", "Extension"),
    ("role", "Role"),
    ("permissions", "Permissions"),
    ("dateAdded", "Created"),
]


@click.group()
def users():
    """Manage users and team members."""
    pass


@users.command("list")
@click.option("--limit", "-l", default=20, help="Number of results")
@click.pass_context
def list_users(ctx, limit: int):
    """List users in the location."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.get("/users/", params={"limit": limit})
        users_list = response.get("users", [])

        output_data(
            users_list,
            columns=USER_COLUMNS,
            format=output_format,
            title="Users",
        )


@users.command("get")
@click.argument("user_id")
@click.pass_context
def get_user(ctx, user_id: str):
    """Get user details."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.get(f"/users/{user_id}")
        user = response.get("user", response)

        output_data(user, format=output_format, single_fields=USER_FIELDS)


@users.command("me")
@click.pass_context
def get_current_user(ctx):
    """Get the current authenticated user."""
    token = get_token()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token) as client:
        response = client.get("/users/me")
        user = response.get("user", response)

        output_data(user, format=output_format, single_fields=USER_FIELDS)


@users.command("search")
@click.argument("query")
@click.option("--limit", "-l", default=20, help="Number of results")
@click.pass_context
def search_users(ctx, query: str, limit: int):
    """Search for users by name or email."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.get("/users/search", params={"query": query, "limit": limit})
        users_list = response.get("users", [])

        output_data(
            users_list,
            columns=USER_COLUMNS,
            format=output_format,
            title=f"Users matching '{query}'",
        )
