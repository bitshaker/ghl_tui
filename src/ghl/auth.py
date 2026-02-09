"""Authentication handling for GHL CLI."""

from typing import Optional

import click

from .config import config_manager


class AuthError(Exception):
    """Authentication error."""

    pass


def get_token() -> str:
    """
    Get the API token, raising an error if not configured.

    Returns:
        The API token string.

    Raises:
        AuthError: If no token is configured.
    """
    token = config_manager.get_token()
    if not token:
        raise AuthError(
            "No API token configured. Run 'ghl config set-token' to set your token, "
            "or set the GHL_API_TOKEN environment variable."
        )
    return token


def require_token(func):
    """Decorator to require authentication for a command."""

    @click.pass_context
    def wrapper(ctx, *args, **kwargs):
        try:
            ctx.ensure_object(dict)
            ctx.obj["token"] = get_token()
            return ctx.invoke(func, *args, **kwargs)
        except AuthError as e:
            raise click.ClickException(str(e))

    return wrapper


def get_location_id() -> str:
    """
    Get the location ID, raising an error if not configured.

    Returns:
        The location ID string.

    Raises:
        AuthError: If no location ID is configured.
    """
    location_id = config_manager.get_location_id()
    if not location_id:
        raise AuthError(
            "No location ID configured. Run 'ghl config set-location <location_id>' "
            "to set your default location, or set the GHL_LOCATION_ID environment variable."
        )
    return location_id


def require_location(func):
    """Decorator to require location ID for a command."""

    @click.pass_context
    def wrapper(ctx, *args, **kwargs):
        try:
            ctx.ensure_object(dict)
            ctx.obj["location_id"] = get_location_id()
            return ctx.invoke(func, *args, **kwargs)
        except AuthError as e:
            raise click.ClickException(str(e))

    return wrapper
