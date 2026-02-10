"""Header bar with location and rate limit status."""

from __future__ import annotations

import time
from typing import Optional

from textual.widgets import Static


class HeaderBar(Static):
    """Shows app title, location name (profile or ID), and API rate limit (remaining/limit, reset)."""

    DEFAULT_CSS = """
    HeaderBar {
        height: 1;
        padding: 0 1;
        background: $surface-darken-1;
        color: $text;
    }
    """

    def __init__(
        self,
        location_label: str = "",
        *,
        id: str | None = "header_bar",
        **kwargs,
    ) -> None:
        super().__init__(id=id, **kwargs)
        self._location_label = location_label or ""
        self._rate_limit_info: Optional[object] = None

    def render(self) -> str:
        loc = (self._location_label[:20] + "…") if len(self._location_label) > 20 else self._location_label or "—"
        rate = "—"
        if self._rate_limit_info is not None and hasattr(self._rate_limit_info, "remaining"):
            rli = self._rate_limit_info
            remaining = getattr(rli, "remaining", 0)
            limit = getattr(rli, "limit", 100)
            reset = getattr(rli, "reset", None)
            if reset:
                secs = max(0, reset - time.time())
                reset_s = f" reset {secs:.1f}s" if secs > 0 else ""
            else:
                reset_s = ""
            rate = f"{remaining}/{limit}{reset_s}"
        return f" GHL TUI  │  Location: {loc}  │  Rate: {rate} "

    def update_location(self, location_label: str) -> None:
        """Update the displayed location name (e.g. profile name)."""
        self._location_label = location_label or ""
        self.refresh()

    def update_rate_limit(self, rate_limit_info: Optional[object]) -> None:
        """Update rate limit from API response (call after each request)."""
        self._rate_limit_info = rate_limit_info
        self.refresh()
