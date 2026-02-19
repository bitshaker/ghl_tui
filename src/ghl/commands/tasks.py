"""Tasks (location-level search) commands."""

from typing import Optional

import click

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..config import config_manager
from ..options import output_format_options
from ..output import output_data
from ..services import tasks as tasks_svc

TASK_COLUMNS = [
    ("id", "ID"),
    ("title", "Title"),
    ("body", "Description"),
    ("dueDate", "Due Date"),
    ("completed", "Completed"),
    ("contactName", "Contact"),
    ("assigneeName", "Assignee"),
]


@click.group()
@output_format_options
def tasks():
    """Search and list tasks at location level (location task search API)."""
    pass


@tasks.command("search")
@output_format_options
@click.option("--assignee", "-a", "assignee_id", help="Filter by assignee user ID")
@click.option(
    "--status",
    "-s",
    type=click.Choice(["all", "pending", "completed"], case_sensitive=False),
    default="all",
    help="Filter by status (default: all)",
)
@click.option("--query", "-q", help="Search tasks by name/text")
@click.option("--limit", "-l", type=int, help="Max results")
@click.option("--skip", type=int, help="Pagination offset")
@click.pass_context
def search_cmd(
    ctx,
    assignee_id: Optional[str],
    status: str,
    query: Optional[str],
    limit: Optional[int],
    skip: Optional[int],
):
    """Search tasks for the current location."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    status_param = None if status == "all" else status

    with GHLClient(token, location_id) as client:
        tasks_list = tasks_svc.search_tasks(
            client,
            location_id,
            assignee_id=assignee_id or None,
            status=status_param,
            query=query.strip() if query else None,
            limit=limit,
            skip=skip,
        )

        output_data(
            tasks_list,
            columns=TASK_COLUMNS,
            format=output_format,
            title="Tasks",
        )
