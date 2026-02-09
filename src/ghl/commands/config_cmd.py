"""Configuration commands for GHL CLI."""

import click

from ..config import config_manager
from ..output import console, print_success


@click.group()
def config():
    """Manage CLI configuration."""
    pass


@config.command("set-token")
@click.option("--keyring", is_flag=True, help="Store token in system keyring")
@click.argument("token", required=False)
def set_token(token: str, keyring: bool):
    """Set the API token for authentication.

    You can provide the token as an argument or enter it interactively.
    The token is stored securely in ~/.ghl/credentials.json or system keyring.
    """
    if not token:
        token = click.prompt("Enter your GoHighLevel API token", hide_input=True)

    if not token or not token.strip():
        raise click.ClickException("Token cannot be empty")

    config_manager.set_token(token.strip(), use_keyring=keyring)
    print_success("API token saved successfully")


@config.command("set-location")
@click.argument("location_id")
def set_location(location_id: str):
    """Set the default location (sub-account) ID.

    Most GHL API operations require a location ID. This sets the default
    so you don't need to specify it for every command.
    """
    config_manager.update_config(location_id=location_id)
    print_success(f"Default location set to: {location_id}")


@config.command("set-format")
@click.argument("format", type=click.Choice(["table", "json", "csv"]))
def set_format(format: str):
    """Set the default output format."""
    config_manager.update_config(output_format=format)
    print_success(f"Default output format set to: {format}")


@config.command("show")
def show():
    """Show current configuration."""
    cfg = config_manager.config
    token = config_manager.get_token()

    console.print("\n[bold]GHL CLI Configuration[/bold]\n")
    console.print(f"  [cyan]Location ID:[/cyan]    {cfg.location_id or '[dim]Not set[/dim]'}")
    console.print(f"  [cyan]API Version:[/cyan]    {cfg.api_version}")
    console.print(f"  [cyan]Output Format:[/cyan]  {cfg.output_format}")
    console.print(
        f"  [cyan]API Token:[/cyan]      {'[green]Configured[/green]' if token else '[red]Not set[/red]'}"
    )
    console.print(f"\n  [dim]Config file: {config_manager.CONFIG_FILE}[/dim]")
    console.print()


@config.command("clear")
@click.option("--token", is_flag=True, help="Clear the stored API token")
@click.option("--all", "clear_all", is_flag=True, help="Clear all configuration")
@click.confirmation_option(prompt="Are you sure you want to clear the configuration?")
def clear(token: bool, clear_all: bool):
    """Clear stored configuration."""
    if clear_all:
        config_manager.clear_token()
        if config_manager.CONFIG_FILE.exists():
            config_manager.CONFIG_FILE.unlink()
        print_success("All configuration cleared")
    elif token:
        config_manager.clear_token()
        print_success("API token cleared")
    else:
        raise click.ClickException("Specify --token or --all to clear configuration")
