"""Main Textual TUI application."""

from textual.app import App

from .screens.main_screen import MainScreen


class GHLTUIApp(App):
    """GHL TUI - Interactive interface for GoHighLevel API."""

    TITLE = "GHL TUI"
    BINDINGS = [
        ("q", "quit", "Quit"),
    ]
    CSS = """
    Screen {
        layout: vertical;
    }
    """

    def on_mount(self) -> None:
        """Set up main screen with location from config."""
        from ghl.config import config_manager
        location_id = config_manager.get_location_id() or ""
        self.push_screen(MainScreen(location_id=location_id))


def run_tui() -> None:
    """Run the TUI application."""
    app = GHLTUIApp()
    app.run()
