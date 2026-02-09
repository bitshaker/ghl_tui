"""Shared CLI option decorators."""

import click


def _merge_output_format(ctx: click.Context, _param: click.Parameter, value: str | None) -> None:
    """Callback: when --json/--csv/--quiet is passed, store in context."""
    if value is not None:
        ctx.ensure_object(dict)
        ctx.obj["output_format"] = value


def output_format_options(f):
    """Add --json, --csv, --quiet to a command/group so they work after the command name."""
    f = click.option(
        "--json",
        "output_format",
        flag_value="json",
        default=None,
        expose_value=False,
        callback=_merge_output_format,
        help="Output as JSON",
    )(f)
    f = click.option(
        "--csv",
        "output_format",
        flag_value="csv",
        default=None,
        expose_value=False,
        callback=_merge_output_format,
        help="Output as CSV",
    )(f)
    f = click.option(
        "--quiet",
        "output_format",
        flag_value="quiet",
        default=None,
        expose_value=False,
        callback=_merge_output_format,
        help="Output only IDs",
    )(f)
    return f
