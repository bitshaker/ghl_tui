"""Tag management commands."""

import click

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..config import config_manager
from ..output import output_data, print_success

TAG_COLUMNS = [
    ("id", "ID"),
    ("name", "Name"),
]


@click.group()
def tags():
    """Manage tags."""
    pass


@tags.command("list")
@click.pass_context
def list_tags(ctx):
    """List all tags in the location."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.get("/locations/tags")
        tags_list = response.get("tags", [])

        output_data(
            tags_list,
            columns=TAG_COLUMNS,
            format=output_format,
            title="Tags",
        )


@tags.command("create")
@click.argument("name")
@click.pass_context
def create_tag(ctx, name: str):
    """Create a new tag."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.post("/locations/tags", json={"name": name})
        tag = response.get("tag", response)

        if output_format == "quiet":
            click.echo(tag.get("id") or tag.get("name"))
        else:
            print_success(f"Tag created: {name}")


@tags.command("delete")
@click.argument("tag_id")
@click.confirmation_option(prompt="Are you sure you want to delete this tag?")
def delete_tag(tag_id: str):
    """Delete a tag."""
    token = get_token()
    location_id = get_location_id()

    with GHLClient(token, location_id) as client:
        client.delete(f"/locations/tags/{tag_id}")
        print_success(f"Tag deleted: {tag_id}")


@tags.command("get")
@click.argument("tag_id")
@click.pass_context
def get_tag(ctx, tag_id: str):
    """Get tag details."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.get(f"/locations/tags/{tag_id}")
        tag = response.get("tag", response)

        fields = [
            ("id", "ID"),
            ("name", "Name"),
            ("dateAdded", "Created"),
        ]

        output_data(tag, format=output_format, single_fields=fields)
