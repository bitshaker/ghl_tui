"""Minimal TUI smoke tests: app and main screen compose without error."""

import pytest

from ghl.tui.app import GHLTUIApp
from ghl.tui.screens.main_screen import MainScreen
from ghl.tui.screens.contacts import ContactsView
from ghl.tui.screens.pipeline_board import PipelineBoardView
from ghl.tui.widgets.rate_limit import HeaderBar


def test_tui_app_imports():
    """TUI app and screens can be imported."""
    assert GHLTUIApp is not None
    assert MainScreen is not None
    assert ContactsView is not None
    assert PipelineBoardView is not None
    assert HeaderBar is not None


def test_header_bar_render():
    """HeaderBar renders without error."""
    bar = HeaderBar(location_id="loc123")
    bar._rate_limit_info = None
    text = bar.render()
    assert "GHL TUI" in text
    assert "loc123" in text


def test_main_screen_compose():
    """MainScreen composes without error (no config/live API)."""
    screen = MainScreen(location_id="test-loc")
    children = list(screen.compose())
    assert len(children) >= 1
    # Should yield HeaderBar, TabBar, Container, Footer
    assert any(c.__class__.__name__ == "HeaderBar" for c in children)


