"""Contact tasks modal: list tasks, add, complete, delete."""

from __future__ import annotations

from datetime import datetime

from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListItem, ListView, Static, TextArea

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..services import contacts as contact_svc


def parse_due_date(value: str) -> str | None:
    """Parse user input into ISO 8601 due date for API. Returns None if empty/invalid."""
    raw = (value or "").strip().replace(" ", "")
    if not raw:
        return None
    try:
        # YYYY-MM-DD or YYYY-MM-DDTHH:MM or YYYY-MM-DDTHH:MM:SS
        if len(raw) >= 19 and "T" in raw[:19]:
            dt = datetime.fromisoformat(raw[:19].replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        elif len(raw) >= 10:
            # Date only: use noon UTC
            dt = datetime.fromisoformat(raw[:10])
            return dt.strftime("%Y-%m-%dT12:00:00Z")
        return None
    except (ValueError, TypeError):
        return None


def format_task_date(due_date: str | None) -> str:
    """Format API datetime for display."""
    if not due_date:
        return ""
    raw = due_date.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw[:10])  # date only
        return dt.strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return due_date[:10] if len(due_date) >= 10 else due_date


def task_display_text(task: dict) -> str:
    """Format a task for list display."""
    title = (task.get("title") or "").strip() or "—"
    body = (task.get("body") or "").strip()
    completed = task.get("completed", False)
    mark = "✓" if completed else "○"
    due = format_task_date(task.get("dueDate"))
    due_str = f"  [dim]{due}[/dim]" if due else ""
    body_preview = ""
    if body:
        preview = body.replace("\n", " ")[:40]
        if len(body.replace("\n", " ")) > 40:
            preview += "…"
        body_preview = f"  [dim]{preview}[/dim]"
    return f" {mark}  {title}{due_str}{body_preview} "


class ContactTasksModal(ModalScreen[None]):
    """Modal showing tasks for a contact with add/complete/delete."""

    CSS = """
    #task-input {
        width: 100%;
    }
    #task-body {
        height: 4;
        width: 100%;
    }
    #task-due {
        width: 100%;
    }
    #task-actions {
        height: auto;
        padding: 0 0 1 0;
    }
    #task-buttons Button {
        margin-right: 2;
    }
    """

    def __init__(self, contact_id: str, contact_name: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._contact_id = contact_id
        self._contact_name = (contact_name or "").strip() or None
        self._tasks: list[dict] = []
        self._selected_index: int = -1

    def compose(self):
        with Vertical():
            if self._contact_name:
                yield Label(f"Tasks — {self._contact_name}", id="tasks-title")
            else:
                yield Label("Tasks", id="tasks-title")
            yield ListView(id="contact-tasks-list")
            yield Static("Add a new task:", id="task-add-label")
            yield Input(placeholder="Title (required)…", id="task-input")
            yield TextArea(placeholder="Body (optional)…", id="task-body")
            yield Input(
                placeholder="Due date (optional, YYYY-MM-DD or YYYY-MM-DDTHH:MM)…",
                id="task-due",
            )
            yield Static("", id="task-actions")
            with Horizontal(id="task-buttons"):
                yield Button("Add task", id="task-add")
                yield Button("Toggle complete", id="task-complete")
                yield Button("Delete task", id="task-delete")
                yield Button("Close", id="tasks-close")

    def on_mount(self) -> None:
        self._load_tasks()
        self.query_one("#task-input", Input).focus()

    def _load_tasks(self) -> None:
        with GHLClient(get_token(), get_location_id()) as client:
            self._tasks = contact_svc.list_tasks(client, self._contact_id)
        lst = self.query_one("#contact-tasks-list", ListView)
        lst.clear()
        for t in self._tasks:
            lst.append(ListItem(Label(task_display_text(t))))
        self._update_actions_visibility()

    def _update_actions_visibility(self) -> None:
        actions = self.query_one("#task-actions", Static)
        complete_btn = self.query_one("#task-complete", Button)
        delete_btn = self.query_one("#task-delete", Button)
        if 0 <= self._selected_index < len(self._tasks):
            task = self._tasks[self._selected_index]
            completed = task.get("completed", False)
            complete_btn.label = "Mark incomplete" if completed else "Mark complete"
            complete_btn.disabled = False
            delete_btn.disabled = False
            lines = [f"Selected: {task.get('title', '—')}"]
            if task.get("dueDate"):
                lines.append(f"Due: {format_task_date(task['dueDate'])}")
            if task.get("body"):
                body = (task.get("body") or "").strip()
                lines.append(f"Body: {body[:200]}{'…' if len(body) > 200 else ''}")
            actions.update("\n".join(lines))
        else:
            complete_btn.disabled = True
            delete_btn.disabled = True
            actions.update("Select a task to complete or delete")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self._selected_index = event.list_view.index
        self._update_actions_visibility()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "tasks-close":
            self.dismiss(None)
        elif event.button.id == "task-add":
            inp = self.query_one("#task-input", Input)
            body_area = self.query_one("#task-body", TextArea)
            due_inp = self.query_one("#task-due", Input)
            title = inp.value.strip()
            if not title:
                self.notify("Enter a task title", severity="warning")
                return
            body = body_area.text.strip() or None
            due_date = parse_due_date(due_inp.value)
            with GHLClient(get_token(), get_location_id()) as client:
                contact_svc.create_task(
                    client, self._contact_id, title, body=body, due_date=due_date
                )
            inp.clear()
            body_area.clear()
            due_inp.clear()
            self._load_tasks()
            self.app.notify("Task added")
        elif event.button.id == "task-complete":
            if 0 <= self._selected_index < len(self._tasks):
                task = self._tasks[self._selected_index]
                completed = not task.get("completed", False)
                with GHLClient(get_token(), get_location_id()) as client:
                    contact_svc.update_task_completed(
                        client, self._contact_id, task["id"], completed
                    )
                self._load_tasks()
                self.app.notify("Task updated")
                self._selected_index = min(self._selected_index, len(self._tasks) - 1)
                self._update_actions_visibility()
        elif event.button.id == "task-delete":
            if 0 <= self._selected_index < len(self._tasks):
                task = self._tasks[self._selected_index]
                with GHLClient(get_token(), get_location_id()) as client:
                    contact_svc.delete_task(client, self._contact_id, task["id"])
                self._load_tasks()
                self.app.notify("Task deleted")
                self._selected_index = min(self._selected_index, len(self._tasks) - 1)
                if self._selected_index < 0:
                    self._selected_index = -1
                self._update_actions_visibility()
