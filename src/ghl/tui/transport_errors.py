"""httpx transport failures from threaded Textual workers (offline, DNS, timeouts)."""

from __future__ import annotations

from typing import Any, Optional

import httpx


def transport_error_toast_message(exc: BaseException) -> Optional[str]:
    """User-facing toast text for common connectivity failures."""
    if isinstance(exc, httpx.ConnectError):
        return "No internet connection — could not reach the API."
    if isinstance(exc, httpx.TimeoutException):
        return "Request timed out — check your network connection."
    if isinstance(exc, httpx.TransportError):
        return "Network error — check your internet connection."
    return None


def notify_transport_error(widget: Any, exc: BaseException) -> bool:
    """
    If ``exc`` is an httpx transport failure, enqueue a toast from a worker thread.

    Returns True when ``exc`` was handled (including when notify could not be sent).
    """
    msg = transport_error_toast_message(exc)
    if msg is None:
        return False
    app = getattr(widget, "app", None)
    if app is None:
        return True
    try:
        app.call_from_thread(lambda m=msg, w=widget: w.notify(m, severity="error"))
    except Exception:
        pass
    return True
