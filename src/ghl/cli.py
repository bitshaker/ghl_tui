"""Main CLI entry point for GHL CLI."""

# Load .env FIRST before any other imports
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

# Explicitly load .env from current working directory
env_path = Path.cwd() / ".env"
if env_path.exists():
    load_dotenv(env_path)

import click  # noqa: E402

from . import __version__  # noqa: E402
from .auth import AuthError, get_location_id, get_token  # noqa: E402
from .client import APIError  # noqa: E402
from .commands import (  # noqa: E402
    calendars,
    config,
    contacts,
    conversations,
    locations,
    opportunities,
    pipelines,
    tags,
    tasks,
    users,
    workflows,
)
from .commands import (  # noqa: E402
    custom_fields as custom_fields_cmd,
)


@click.group()
@click.version_option(version=__version__)
@click.option("--json", "output_format", flag_value="json", default=None, help="Output as JSON")
@click.option("--csv", "output_format", flag_value="csv", default=None, help="Output as CSV")
@click.option(
    "--quiet", "-q", "output_format", flag_value="quiet", default=None, help="Output only IDs"
)
@click.pass_context
def main(ctx, output_format=None):
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
    if output_format is not None:
        ctx.obj["output_format"] = output_format


# Register command groups
main.add_command(config)
main.add_command(contacts)
main.add_command(calendars)
main.add_command(custom_fields_cmd)
main.add_command(opportunities)
main.add_command(conversations)
main.add_command(workflows)
main.add_command(locations)
main.add_command(users)
main.add_command(tags)
main.add_command(tasks)
main.add_command(pipelines)


@click.command("tui")
def tui_cmd():
    """Launch the interactive TUI (contacts, pipeline board)."""
    try:
        get_token()
        get_location_id()
    except AuthError as e:
        raise click.ClickException(str(e))
    from .tui.app import run_tui
    run_tui()


main.add_command(tui_cmd)


@main.command("completion")
@click.option(
    "--shell",
    "-s",
    type=click.Choice(["bash", "zsh", "fish"], case_sensitive=False),
    help="Shell to generate completion for. If omitted, prints setup instructions.",
)
def completion_cmd(shell):
    """Show shell completion setup so you can see command options with Tab.

    Enable tab completion to see subcommands (e.g. config, contacts, calendars)
    and options as you type. Run once with your shell, then add the suggested
    line to your shell config (~/.bashrc, ~/.zshrc, or config.fish).

    Example (zsh):
      eval \"$(ghl completion --shell zsh)\"
    """
    if shell is None:
        click.echo("Shell completion lets you press Tab to see commands and options.")
        click.echo()
        click.echo("Ways to enable (you don't have to use .zshrc):")
        click.echo()
        click.echo("  1. This terminal only - run once in this session:")
        click.echo("     eval \"$(ghl completion --shell zsh)\"")
        click.echo()
        click.echo("  2. Permanent - add that line to ~/.zshrc (or ~/.bashrc / fish config).")
        click.echo()
        click.echo("  3. On demand - save and source when needed:")
        click.echo("     ghl completion --shell zsh > ~/.ghl-complete.zsh")
        click.echo("     source ~/.ghl-complete.zsh   # when you want completion")
        click.echo()
        click.echo("Replace zsh with bash or fish if you use another shell.")
        return

    env = {**os.environ, "_GHL_COMPLETE": f"{shell}_source"}
    for cmd in (["ghl"], [sys.executable, "-m", "ghl"]):
        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=10,
            )
            break
        except FileNotFoundError:
            continue
    else:
        click.echo(
            "Could not find 'ghl' in PATH. Install with 'pip install -e .' and ensure 'ghl' is on PATH.",
            err=True,
        )
        raise SystemExit(1)

    if result.returncode != 0 and result.stderr:
        click.echo(result.stderr, err=True)
    click.echo(result.stdout)


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
