"""Minimal TUI smoke tests: app and main screen compose without error."""

import pytest

from ghl.tui.app import GHLTUIApp
from ghl.tui.screens.calendar import (
    _cell,
    _format_event_time,
    _parse_api_datetime_string,
)
from ghl.tui.screens.main_screen import MainScreen
from ghl.tui.screens.contacts import ContactsView
from ghl.tui.screens.calendar import CalendarView
from ghl.tui.screens.pipeline_board import PipelineBoardView
from ghl.tui.widgets.rate_limit import HeaderBar


def test_tui_app_imports():
    """TUI app and screens can be imported."""
    assert GHLTUIApp is not None
    assert MainScreen is not None
    assert ContactsView is not None
    assert PipelineBoardView is not None
    assert CalendarView is not None
    assert HeaderBar is not None


def test_header_bar_render():
    """HeaderBar renders without error."""
    bar = HeaderBar(location_label="work")
    bar._rate_limit_info = None
    text = bar.render()
    assert "GHL TUI" in text
    assert "Location: work" in text


def test_format_event_time_ghl_offset_string():
    """GHL returns startTime like 2026-03-25T10:00:00-07:00 (offset with colon)."""
    out = _format_event_time("2026-03-25T10:00:00-07:00")
    assert out != "—"
    assert len(out) >= 10


def test_parse_api_datetime_string_offset():
    dt = _parse_api_datetime_string("2026-03-25T10:00:00-07:00")
    assert dt is not None
    assert dt.hour == 10


def test_calendar_table_cell_plain_brackets():
    """DataTable cells use Rich Text so '[' in API strings is not parsed as markup."""
    t = _cell("Meet [VIP] client")
    assert "[VIP]" in t.plain


def test_main_screen_compose():
    """MainScreen composes without error (no config/live API)."""
    screen = MainScreen(location_label="test-loc")
    children = list(screen.compose())
    assert len(children) >= 1
    # Should yield HeaderBar, TabBar, Container, Footer
    assert any(c.__class__.__name__ == "HeaderBar" for c in children)


