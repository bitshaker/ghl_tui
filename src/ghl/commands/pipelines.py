"""Pipeline management commands."""

import click

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..config import config_manager
from ..output import output_data

PIPELINE_COLUMNS = [
    ("id", "ID"),
    ("name", "Name"),
]

STAGE_COLUMNS = [
    ("id", "ID"),
    ("name", "Name"),
    ("position", "Position"),
]


@click.group()
def pipelines():
    """Manage pipelines and stages."""
    pass


@pipelines.command("list")
@click.pass_context
def list_pipelines(ctx):
    """List all pipelines."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.get("/opportunities/pipelines")
        pipelines_list = response.get("pipelines", [])

        output_data(
            pipelines_list,
            columns=PIPELINE_COLUMNS,
            format=output_format,
            title="Pipelines",
        )


@pipelines.command("get")
@click.argument("pipeline_id")
@click.pass_context
def get_pipeline(ctx, pipeline_id: str):
    """Get pipeline details including stages."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.get(f"/opportunities/pipelines/{pipeline_id}")
        pipeline = response.get("pipeline", response)

        if output_format == "json":
            output_data(pipeline, format="json")
        else:
            fields = [
                ("id", "ID"),
                ("name", "Name"),
                ("locationId", "Location ID"),
            ]
            output_data(pipeline, format=output_format, single_fields=fields)

            # Also display stages if available
            stages = pipeline.get("stages", [])
            if stages:
                click.echo("\nStages:")
                output_data(
                    stages,
                    columns=STAGE_COLUMNS,
                    format=output_format,
                )


@pipelines.command("stages")
@click.argument("pipeline_id")
@click.pass_context
def list_stages(ctx, pipeline_id: str):
    """List stages in a pipeline."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.get(f"/opportunities/pipelines/{pipeline_id}")
        pipeline = response.get("pipeline", response)
        stages = pipeline.get("stages", [])

        output_data(
            stages,
            columns=STAGE_COLUMNS,
            format=output_format,
            title=f"Stages in Pipeline: {pipeline.get('name', pipeline_id)}",
        )
