"""Location (sub-account) management commands."""

import click

from ..auth import get_token
from ..client import GHLClient
from ..config import config_manager
from ..output import output_data, print_success

LOCATION_COLUMNS = [
    ("id", "ID"),
    ("name", "Name"),
    ("email", "Email"),
    ("phone", "Phone"),
    ("address", "Address"),
]

LOCATION_FIELDS = [
    ("id", "ID"),
    ("name", "Name"),
    ("email", "Email"),
    ("phone", "Phone"),
    ("address", "Address"),
    ("city", "City"),
    ("state", "State"),
    ("postalCode", "Postal Code"),
    ("country", "Country"),
    ("website", "Website"),
    ("timezone", "Timezone"),
    ("dateAdded", "Created"),
]


@click.group()
def locations():
    """Manage locations (sub-accounts)."""
    pass


@locations.command("list")
@click.option("--company", "-c", "company_id", help="Filter by company/agency ID")
@click.option("--limit", "-l", default=20, help="Number of results")
@click.option("--skip", "-s", default=0, help="Number to skip")
@click.pass_context
def list_locations(ctx, company_id: str, limit: int, skip: int):
    """List locations."""
    token = get_token()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token) as client:
        params = {"limit": limit, "skip": skip}
        if company_id:
            params["companyId"] = company_id

        # Remove default location ID for this call
        response = client.request("GET", "/locations/search", params=params)
        locations_list = response.get("locations", [])

        output_data(
            locations_list,
            columns=LOCATION_COLUMNS,
            format=output_format,
            title="Locations",
        )


@locations.command("get")
@click.argument("location_id")
@click.pass_context
def get_location(ctx, location_id: str):
    """Get location details."""
    token = get_token()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token) as client:
        response = client.get(f"/locations/{location_id}")
        location = response.get("location", response)

        output_data(location, format=output_format, single_fields=LOCATION_FIELDS)


@locations.command("switch")
@click.argument("location_id")
def switch_location(location_id: str):
    """Switch to a different default location."""
    config_manager.update_config(location_id=location_id)
    print_success(f"Switched to location: {location_id}")


@locations.command("current")
def current_location():
    """Show the current default location."""
    location_id = config_manager.get_location_id()
    if location_id:
        click.echo(f"Current location: {location_id}")
    else:
        click.echo("No default location set. Use 'ghl locations switch <id>' to set one.")
