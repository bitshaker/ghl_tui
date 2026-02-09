"""Workflow management commands."""

import click

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..config import config_manager
from ..output import output_data, print_success

WORKFLOW_COLUMNS = [
    ("id", "ID"),
    ("name", "Name"),
    ("status", "Status"),
    ("version", "Version"),
]


@click.group()
def workflows():
    """Manage workflows and automations."""
    pass


@workflows.command("list")
@click.pass_context
def list_workflows(ctx):
    """List all workflows."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.get("/workflows/")
        workflows_list = response.get("workflows", [])

        output_data(
            workflows_list,
            columns=WORKFLOW_COLUMNS,
            format=output_format,
            title="Workflows",
        )


@workflows.command("get")
@click.argument("workflow_id")
@click.pass_context
def get_workflow(ctx, workflow_id: str):
    """Get workflow details."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.get(f"/workflows/{workflow_id}")
        workflow = response.get("workflow", response)

        fields = [
            ("id", "ID"),
            ("name", "Name"),
            ("status", "Status"),
            ("version", "Version"),
            ("createdAt", "Created"),
            ("updatedAt", "Updated"),
        ]

        output_data(workflow, format=output_format, single_fields=fields)


@workflows.command("trigger")
@click.argument("workflow_id")
@click.option("--contact", "-c", "contact_id", required=True, help="Contact ID to enroll")
def trigger_workflow(workflow_id: str, contact_id: str):
    """Trigger a workflow for a contact."""
    token = get_token()
    location_id = get_location_id()

    with GHLClient(token, location_id) as client:
        # The workflow trigger endpoint enrolls a contact into a workflow
        response = client.post(
            f"/workflows/{workflow_id}/enroll",
            json={"contactId": contact_id},
        )

        # Check if enrollment was successful
        if response.get("success") or response.get("enrolled"):
            print_success(f"Contact {contact_id} enrolled in workflow {workflow_id}")
        else:
            print_success(f"Workflow trigger sent for contact {contact_id}")
