"""Main CLI entry point for GHL CLI."""

# Load .env FIRST before any other imports
import os
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load .env from current working directory
env_path = Path.cwd() / ".env"
if env_path.exists():
    load_dotenv(env_path)

import click

from . import __version__
from .auth import AuthError
from .client import APIError
from .commands import (
    calendars,
    config,
    contacts,
    conversations,
    locations,
    opportunities,
    pipelines,
    tags,
    users,
    workflows,
)


@click.group()
@click.version_option(version=__version__)
@click.option("--json", "output_format", flag_value="json", help="Output as JSON")
@click.option("--csv", "output_format", flag_value="csv", help="Output as CSV")
@click.option("--quiet", "-q", "output_format", flag_value="quiet", help="Output only IDs")
@click.pass_context
def main(ctx, output_format):
    """GoHighLevel CLI - Command-line interface for GoHighLevel API v2.

    Manage contacts, calendars, opportunities, conversations, and more
    from the command line.

    \b
    Quick Start:
      1. Run 'ghl config set-token' to configure your API token
      2. Run 'ghl config set-location <location_id>' to set your default location
      3. Run 'ghl contacts list' to verify everything works

    \b
    For more information on getting your API token, see:
    https://highlevel.stoplight.io/docs/integrations/
    """
    ctx.ensure_object(dict)
    ctx.obj["output_format"] = output_format


# Register command groups
main.add_command(config)
main.add_command(contacts)
main.add_command(calendars)
main.add_command(opportunities)
main.add_command(conversations)
main.add_command(workflows)
main.add_command(locations)
main.add_command(users)
main.add_command(tags)
main.add_command(pipelines)


def cli():
    """Entry point with error handling."""
    try:
        main(standalone_mode=False)
    except click.ClickException as e:
        e.show()
        raise SystemExit(1)
    except (APIError, AuthError) as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    except click.Abort:
        click.echo("Aborted!", err=True)
        raise SystemExit(1)
    except KeyboardInterrupt:
        click.echo("Aborted!", err=True)
        raise SystemExit(130)


if __name__ == "__main__":
    cli()
