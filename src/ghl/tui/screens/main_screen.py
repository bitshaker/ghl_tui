"""Main screen: header, tab bar, content area, footer."""

from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Static

from ..widgets.rate_limit import HeaderBar


class TabBar(Static):
    """Simple tab bar for Contacts | Pipeline Board."""

    DEFAULT_CSS = """
    TabBar {
        height: 1;
        padding: 0 1;
        background: $surface;
    }
    .tab-active {
        text-style: bold;
        color: $primary;
    }
    .tab-inactive {
        color: $text-muted;
    }
    """

    def __init__(self, active: str = "contacts", **kwargs) -> None:
        super().__init__(**kwargs)
        self._active = active

    def render(self) -> str:
        if self._active == "contacts":
            return "  * Contacts  |  Pipeline Board  "
        return "  Contacts  |  * Pipeline Board  "

    def set_active(self, tab: str) -> None:
        self._active = tab
        self.refresh()


class MainScreen(Screen):
    """Single main screen with header, tabs, content area, footer."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("1", "show_contacts", "Contacts"),
        ("2", "show_pipeline", "Pipeline"),
    ]

    CSS = """
    MainScreen {
        layout: vertical;
    }
    #content {
        width: 100%;
        height: auto;
        min-height: 1;
    }
    """

    def __init__(self, location_label: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._location_label = location_label or ""
        self._current_tab = "contacts"

    def compose(self):
        yield HeaderBar(location_label=self._location_label, id="header_bar")
        yield TabBar(active=self._current_tab, id="tab_bar")
        yield Container(id="content")
        yield Footer()

    def get_header_bar(self) -> HeaderBar:
        return self.query_one("#header_bar", HeaderBar)

    def get_tab_bar(self) -> TabBar:
        return self.query_one("#tab_bar", TabBar)

    def get_content(self) -> Container:
        return self.query_one("#content", Container)

    def action_show_contacts(self) -> None:
        self._switch_tab("contacts")

    def action_show_pipeline(self) -> None:
        self._switch_tab("pipeline")

    def _switch_tab(self, tab: str) -> None:
        if tab == self._current_tab:
            return
        self._current_tab = tab
        self.get_tab_bar().set_active(tab)
        content = self.get_content()
        content.remove_children()
        if tab == "contacts":
            from .contacts import ContactsView
            content.mount(ContactsView())
        else:
            from .pipeline_board import PipelineBoardView
            content.mount(PipelineBoardView())

    def on_mount(self) -> None:
        from .contacts import ContactsView
        self.get_content().mount(ContactsView())
