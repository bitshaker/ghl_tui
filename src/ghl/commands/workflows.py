"""Workflow management commands."""

from typing import Optional

import click

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..config import config_manager
from ..options import output_format_options
from ..output import output_data, print_success
from ..services import workflows as workflow_svc

WORKFLOW_COLUMNS = [
    ("id", "ID"),
    ("name", "Name"),
    ("status", "Status"),
    ("version", "Version"),
]

WORKFLOW_DETAIL_FIELDS = [
    ("id", "ID"),
    ("name", "Name"),
    ("status", "Status"),
    ("version", "Version"),
    ("createdAt", "Created"),
    ("updatedAt", "Updated"),
]


@click.group()
@output_format_options
def workflows():
    """Manage workflows and automations."""
    pass


@workflows.command("list")
@output_format_options
@click.pass_context
def list_workflows(ctx):
    """List all workflows."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        workflows_list = workflow_svc.list_workflows(client)

        output_data(
            workflows_list,
            columns=WORKFLOW_COLUMNS,
            format=output_format,
            title="Workflows",
        )


@workflows.command("get")
@output_format_options
@click.argument("workflow_id")
@click.pass_context
def get_workflow(ctx, workflow_id: str):
    """Get workflow details (resolved from the workflows list API)."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        try:
            workflow = workflow_svc.get_workflow(client, workflow_id)
        except LookupError:
            raise click.ClickException(f"Workflow not found: {workflow_id}") from None

        output_data(workflow, format=output_format, single_fields=WORKFLOW_DETAIL_FIELDS)


@workflows.command("trigger")
@click.argument("workflow_id")
@click.option("--contact", "-c", "contact_id", required=True, help="Contact ID to enroll")
@click.option(
    "--event-start-time",
    help="Optional ISO-8601 start time for wait/timer steps (eventStartTime)",
)
def trigger_workflow(workflow_id: str, contact_id: str, event_start_time: Optional[str]):
    """Enroll a contact in a workflow."""
    token = get_token()
    location_id = get_location_id()

    with GHLClient(token, location_id) as client:
        response = workflow_svc.add_contact_to_workflow(
            client,
            contact_id,
            workflow_id,
            event_start_time=event_start_time,
        )
        if workflow_svc.enrollment_succeeded(response):
            print_success(f"Contact {contact_id} enrolled in workflow {workflow_id}")
        else:
            print_success(f"Workflow enrollment sent for contact {contact_id}")
