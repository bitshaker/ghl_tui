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


@click.group("profiles")
def profiles_group():
    """Manage GHL location profiles (token + location ID pairs). Switch with 'use'."""
    pass


@profiles_group.command("list")
def profiles_list():
    """List all profiles and show which one is active (used by default)."""
    items = config_manager.list_profiles()
    if not items:
        console.print(
            "\n[dim]No profiles yet. Add one with: ghl config profiles add <name>[/dim]\n"
        )
        return
    console.print("\n[bold]Profiles[/bold]\n")
    for name, is_active in items:
        mark = " [green]*[/green]" if is_active else ""
        console.print(f"  {name}{mark}")
    console.print("\n  [dim]* = active (used by default)[/dim]\n")


@profiles_group.command("add")
@click.argument("name")
@click.option("--token", "-t", help="API token (prompted if omitted)")
@click.option("--location-id", "-l", "location_id", help="Location ID (prompted if omitted)")
def profiles_add(name: str, token: str, location_id: str):
    """Add a profile (or update if name exists). Becomes active if none selected."""
    if not token:
        token = click.prompt("API token", hide_input=True)
    if not location_id:
        location_id = click.prompt("Location ID")
    if not token or not token.strip():
        raise click.ClickException("Token cannot be empty")
    if not location_id or not location_id.strip():
        raise click.ClickException("Location ID cannot be empty")
    config_manager.add_or_update_profile(name.strip(), token.strip(), location_id.strip())
    print_success(f"Profile '{name}' saved and set as active")


@profiles_group.command("use")
@click.argument("name")
def profiles_use(name: str):
    """Switch to this profile. This choice is remembered for next time."""
    try:
        config_manager.set_active_profile(name)
    except ValueError as e:
        raise click.ClickException(str(e))
    print_success(f"Switched to profile: {name}")


@profiles_group.command("remove")
@click.argument("name")
@click.confirmation_option(prompt="Remove this profile?")
def profiles_remove(name: str):
    """Remove a profile."""
    try:
        config_manager.remove_profile(name)
    except ValueError as e:
        raise click.ClickException(str(e))
    print_success(f"Profile '{name}' removed")


config.add_command(profiles_group)


@config.command("show")
def show():
    """Show current configuration."""
    cfg = config_manager.config
    token = config_manager.get_token()
    active_profile = config_manager.get_active_profile_name()

    console.print("\n[bold]GHL CLI Configuration[/bold]\n")
    if active_profile:
        console.print(f"  [cyan]Active profile:[/cyan]  [green]{active_profile}[/green]")
    loc = cfg.location_id or config_manager.get_location_id() or "[dim]Not set[/dim]"
    console.print(f"  [cyan]Location ID:[/cyan]    {loc}")
    console.print(f"  [cyan]API Version:[/cyan]    {cfg.api_version}")
    console.print(f"  [cyan]Output Format:[/cyan]  {cfg.output_format}")
    token_status = "[green]Configured[/green]" if token else "[red]Not set[/red]"
    console.print(f"  [cyan]API Token:[/cyan]      {token_status}")
    console.print(f"\n  [dim]Config: {config_manager.CONFIG_FILE}[/dim]")
    console.print(f"  [dim]Profiles: {config_manager.PROFILES_FILE}[/dim]")
    console.print()


@config.command("clear")
@click.option("--token", is_flag=True, help="Clear the stored API token")
@click.option("--all", "clear_all", is_flag=True, help="Clear all configuration")
@click.confirmation_option(prompt="Are you sure you want to clear the configuration?")
def clear(token: bool, clear_all: bool):
    """Clear stored configuration."""
    if clear_all:
        config_manager.clear_token()
        config_manager.clear_profiles()
        if config_manager.CONFIG_FILE.exists():
            config_manager.CONFIG_FILE.unlink()
        print_success("All configuration cleared")
    elif token:
        config_manager.clear_token()
        print_success("API token cleared")
    else:
        raise click.ClickException("Specify --token or --all to clear configuration")
