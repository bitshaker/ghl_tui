"""Output formatting for GHL CLI."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Optional

import click
from rich.console import Console
from rich.table import Table

console = Console()


def format_value(value: Any) -> str:
    """Format a value for display."""
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, list):
        if len(value) == 0:
            return "-"
        if len(value) <= 3:
            return ", ".join(str(v) for v in value)
        return f"{len(value)} items"
    if isinstance(value, dict):
        return json.dumps(value)
    return str(value)


def output_table(
    data: list[dict[str, Any]],
    columns: list[tuple[str, str]],
    title: Optional[str] = None,
) -> None:
    """
    Output data as a rich table.

    Args:
        data: List of dictionaries to display
        columns: List of (key, header) tuples defining columns
        title: Optional table title
    """
    if not data:
        console.print("[dim]No results found.[/dim]")
        return

    table = Table(title=title, show_header=True, header_style="bold cyan")

    for _, header in columns:
        table.add_column(header)

    for row in data:
        values = []
        for key, _ in columns:
            # Support nested keys like "contact.name"
            value = row
            for k in key.split("."):
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    value = None
                    break
            values.append(format_value(value))
        table.add_row(*values)

    console.print(table)


def output_json(data: Any) -> None:
    """Output data as formatted JSON."""
    click.echo(json.dumps(data, indent=2, default=str))


def output_csv(data: list[dict[str, Any]], columns: list[tuple[str, str]]) -> None:
    """
    Output data as CSV.

    Args:
        data: List of dictionaries to display
        columns: List of (key, header) tuples defining columns
    """
    if not data:
        return

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([header for _, header in columns])

    # Write data
    for row in data:
        values = []
        for key, _ in columns:
            value = row
            for k in key.split("."):
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    value = None
                    break
            values.append(format_value(value) if value != "-" else "")
        writer.writerow(values)

    click.echo(output.getvalue().strip())


def output_ids(data: list[dict[str, Any]], id_key: str = "id") -> None:
    """Output only IDs, one per line (for scripting)."""
    for row in data:
        if id_key in row:
            click.echo(row[id_key])


def output_single(data: dict[str, Any], fields: list[tuple[str, str]]) -> None:
    """
    Output a single record with field labels.

    Args:
        data: Dictionary to display
        fields: List of (key, label) tuples defining fields
    """
    max_label_len = max(len(label) for _, label in fields)

    for key, label in fields:
        value = data
        for k in key.split("."):
            if isinstance(value, dict):
                value = value.get(k)
            else:
                value = None
                break
        formatted = format_value(value)
        console.print(f"[bold]{label.ljust(max_label_len)}[/bold]  {formatted}")


def output_data(
    data: Any,
    columns: Optional[list[tuple[str, str]]] = None,
    format: str = "table",
    title: Optional[str] = None,
    id_key: str = "id",
    single_fields: Optional[list[tuple[str, str]]] = None,
) -> None:
    """
    Output data in the specified format.

    Args:
        data: Data to output (list of dicts or single dict)
        columns: Column definitions for table/csv (key, header)
        format: Output format (table, json, csv, quiet)
        title: Optional title for table format
        id_key: Key to use for quiet mode
        single_fields: Field definitions for single record display
    """
    if format == "json":
        output_json(data)
        return

    if format == "quiet":
        if isinstance(data, list):
            output_ids(data, id_key)
        elif isinstance(data, dict) and id_key in data:
            click.echo(data[id_key])
        return

    if isinstance(data, list):
        if format == "csv" and columns:
            output_csv(data, columns)
        elif columns:
            output_table(data, columns, title)
        else:
            output_json(data)
    elif isinstance(data, dict):
        if single_fields:
            output_single(data, single_fields)
        else:
            output_json(data)
    else:
        click.echo(str(data))


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]✗[/red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]![/yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[blue]i[/blue] {message}")
