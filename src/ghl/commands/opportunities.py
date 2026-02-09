"""Opportunity (pipeline) management commands."""

from typing import Optional

import click

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..config import config_manager
from ..output import output_data, print_success

OPPORTUNITY_COLUMNS = [
    ("id", "ID"),
    ("name", "Name"),
    ("contact.name", "Contact"),
    ("pipelineStageId", "Stage ID"),
    ("status", "Status"),
    ("monetaryValue", "Value"),
]

OPPORTUNITY_FIELDS = [
    ("id", "ID"),
    ("name", "Name"),
    ("contact.id", "Contact ID"),
    ("contact.name", "Contact Name"),
    ("contact.email", "Contact Email"),
    ("pipelineId", "Pipeline ID"),
    ("pipelineStageId", "Stage ID"),
    ("status", "Status"),
    ("monetaryValue", "Monetary Value"),
    ("source", "Source"),
    ("dateAdded", "Created"),
    ("dateUpdated", "Updated"),
]


@click.group()
def opportunities():
    """Manage opportunities (pipeline deals)."""
    pass


@opportunities.command("list")
@click.option("--pipeline", "-p", "pipeline_id", help="Filter by pipeline ID")
@click.option("--stage", "-s", "stage_id", help="Filter by stage ID")
@click.option("--status", help="Filter by status (open, won, lost, abandoned)")
@click.option("--contact", "contact_id", help="Filter by contact ID")
@click.option("--limit", "-l", default=20, help="Number of results")
@click.option("--skip", default=0, help="Number to skip")
@click.pass_context
def list_opportunities(
    ctx,
    pipeline_id: Optional[str],
    stage_id: Optional[str],
    status: Optional[str],
    contact_id: Optional[str],
    limit: int,
    skip: int,
):
    """List opportunities."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        params = {"limit": limit, "skip": skip}
        if pipeline_id:
            params["pipelineId"] = pipeline_id
        if stage_id:
            params["pipelineStageId"] = stage_id
        if status:
            params["status"] = status
        if contact_id:
            params["contactId"] = contact_id

        response = client.get("/opportunities/search", params=params)
        opportunities_list = response.get("opportunities", [])

        output_data(
            opportunities_list,
            columns=OPPORTUNITY_COLUMNS,
            format=output_format,
            title="Opportunities",
        )


@opportunities.command("get")
@click.argument("opportunity_id")
@click.pass_context
def get_opportunity(ctx, opportunity_id: str):
    """Get opportunity details."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.get(f"/opportunities/{opportunity_id}")
        opportunity = response.get("opportunity", response)

        output_data(opportunity, format=output_format, single_fields=OPPORTUNITY_FIELDS)


@opportunities.command("create")
@click.option("--contact", "-c", "contact_id", required=True, help="Contact ID")
@click.option("--pipeline", "-p", "pipeline_id", required=True, help="Pipeline ID")
@click.option("--stage", "-s", "stage_id", required=True, help="Pipeline stage ID")
@click.option("--name", "-n", required=True, help="Opportunity name")
@click.option("--value", "-v", type=float, help="Monetary value")
@click.option("--status", default="open", help="Status (open, won, lost, abandoned)")
@click.option("--source", help="Lead source")
@click.pass_context
def create_opportunity(
    ctx,
    contact_id: str,
    pipeline_id: str,
    stage_id: str,
    name: str,
    value: Optional[float],
    status: str,
    source: Optional[str],
):
    """Create a new opportunity."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        data = {
            "contactId": contact_id,
            "pipelineId": pipeline_id,
            "pipelineStageId": stage_id,
            "name": name,
            "status": status,
            "locationId": location_id,
        }

        if value is not None:
            data["monetaryValue"] = value
        if source:
            data["source"] = source

        response = client.post("/opportunities/", json=data)
        opportunity = response.get("opportunity", response)

        if output_format == "quiet":
            click.echo(opportunity.get("id"))
        else:
            print_success(f"Opportunity created: {opportunity.get('id')}")
            output_data(opportunity, format=output_format, single_fields=OPPORTUNITY_FIELDS)


@opportunities.command("update")
@click.argument("opportunity_id")
@click.option("--name", "-n", help="New name")
@click.option("--value", "-v", type=float, help="New monetary value")
@click.option("--status", help="New status (open, won, lost, abandoned)")
@click.option("--source", help="New source")
@click.pass_context
def update_opportunity(
    ctx,
    opportunity_id: str,
    name: Optional[str],
    value: Optional[float],
    status: Optional[str],
    source: Optional[str],
):
    """Update an opportunity."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        data = {}

        if name:
            data["name"] = name
        if value is not None:
            data["monetaryValue"] = value
        if status:
            data["status"] = status
        if source:
            data["source"] = source

        if not data:
            raise click.ClickException("No fields to update. Specify at least one option.")

        response = client.put(f"/opportunities/{opportunity_id}", json=data)
        opportunity = response.get("opportunity", response)

        print_success(f"Opportunity updated: {opportunity_id}")
        output_data(opportunity, format=output_format, single_fields=OPPORTUNITY_FIELDS)


@opportunities.command("move")
@click.argument("opportunity_id")
@click.option("--stage", "-s", "stage_id", required=True, help="Target stage ID")
@click.pass_context
def move_opportunity(ctx, opportunity_id: str, stage_id: str):
    """Move an opportunity to a different stage."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.put(
            f"/opportunities/{opportunity_id}", json={"pipelineStageId": stage_id}
        )
        opportunity = response.get("opportunity", response)

        print_success(f"Opportunity moved to stage: {stage_id}")
        output_data(opportunity, format=output_format, single_fields=OPPORTUNITY_FIELDS)


@opportunities.command("delete")
@click.argument("opportunity_id")
@click.confirmation_option(prompt="Are you sure you want to delete this opportunity?")
def delete_opportunity(opportunity_id: str):
    """Delete an opportunity."""
    token = get_token()
    location_id = get_location_id()

    with GHLClient(token, location_id) as client:
        client.delete(f"/opportunities/{opportunity_id}")
        print_success(f"Opportunity deleted: {opportunity_id}")


@opportunities.command("won")
@click.argument("opportunity_id")
def mark_won(opportunity_id: str):
    """Mark an opportunity as won."""
    token = get_token()
    location_id = get_location_id()

    with GHLClient(token, location_id) as client:
        client.put(f"/opportunities/{opportunity_id}/status", json={"status": "won"})
        print_success(f"Opportunity marked as won: {opportunity_id}")


@opportunities.command("lost")
@click.argument("opportunity_id")
def mark_lost(opportunity_id: str):
    """Mark an opportunity as lost."""
    token = get_token()
    location_id = get_location_id()

    with GHLClient(token, location_id) as client:
        client.put(f"/opportunities/{opportunity_id}/status", json={"status": "lost"})
        print_success(f"Opportunity marked as lost: {opportunity_id}")
