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
        """Set up main screen with location label (profile name or location ID) from config."""
        from ghl.config import config_manager
        profile_name = config_manager.get_active_profile_name()
        location_label = profile_name if profile_name else (config_manager.get_location_id() or "—")
        self.push_screen(MainScreen(location_label=location_label))


def run_tui() -> None:
    """Run the TUI application."""
    app = GHLTUIApp()
    app.run()
