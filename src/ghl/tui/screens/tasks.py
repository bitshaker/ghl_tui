"""Tasks view: location-level task search with filters and DataTable."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from textual import on, work
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Label, Select, Static
from textual.worker import Worker, WorkerState

from ...auth import get_location_id, get_token
from ...client import GHLClient
from ...services import contacts as contact_svc
from ...services import tasks as tasks_svc
from ...services import users as users_svc
from ..contact_tasks import ContactTasksModal, format_task_date


def _task_due_date_parsed(due_date: str | None) -> Optional[datetime]:
    """Parse task dueDate to timezone-aware datetime (UTC). Returns None if missing/invalid."""
    if not due_date or not isinstance(due_date, str):
        return None
    raw = due_date.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        # Parse full ISO if present, else date only
        if "T" in raw[:25]:
            dt = datetime.fromisoformat(raw[:19].replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        return datetime.fromisoformat(raw[:10]).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def _apply_date_filter(tasks: list[dict], preset: str) -> list[dict]:
    """Filter tasks by saved filter preset (client-side). Uses local date for 'today'."""
    if preset == "all":
        return tasks
    today_local = datetime.now().date()
    result = []
    for t in tasks:
        due_dt = _task_due_date_parsed(t.get("dueDate"))
        if due_dt is None:
            if preset == "upcoming":
                result.append(t)
            continue
        due_date_local = due_dt.astimezone().date()
        completed = t.get("completed", False)
        if preset == "due_today":
            if due_date_local == today_local:
                result.append(t)
        elif preset == "overdue":
            if due_date_local < today_local and not completed:
                result.append(t)
        elif preset == "upcoming":
            if due_date_local >= today_local and not completed:
                result.append(t)
    return result


class TasksView(Container):
    """Tasks tab: Assignee/Status filters, saved filter buttons, DataTable."""

    BINDINGS = [
        ("r", "refresh_tasks", "Refresh"),
        ("enter", "toggle_complete", "Toggle complete"),
        ("c", "toggle_complete", "Complete"),
        ("e", "edit_task", "Edit task"),
    ]

    DEFAULT_CSS = """
    TasksView {
        width: 100%;
        height: auto;
        layout: vertical;
    }
    #tasks-toolbar {
        height: auto;
        padding: 0 0 1 0;
    }
    #tasks-filters {
        height: auto;
        padding: 0 0 1 0;
    }
    #tasks-saved {
        height: auto;
        padding: 0 0 1 0;
    }
    #tasks-table {
        height: 1fr;
        min-height: 8;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._tasks: list[dict] = []
        self._assignee_id: Optional[str] = None
        self._status: Optional[str] = None
        self._saved_filter: str = "all"  # all | due_today | overdue | upcoming
        self._users: list[dict] = []
        self._user_name_map: dict[str, str] = {}
        self._contact_name_map: dict[str, str] = {}

    def compose(self):
        with Vertical(id="tasks-toolbar"):
            yield Label("Tasks — location-level search", id="tasks-title")
        with Horizontal(id="tasks-filters"):
            yield Label("Assignee:")
            yield Select([("Any", "")], id="tasks-assignee", allow_blank=True)
            yield Label("Status:")
            yield Select(
                [("All", ""), ("Pending", "pending"), ("Completed", "completed")],
                id="tasks-status",
                allow_blank=True,
            )
        with Horizontal(id="tasks-saved"):
            yield Button("All Tasks", id="saved-all")
            yield Button("Due Today", id="saved-due-today")
            yield Button("Overdue", id="saved-overdue")
            yield Button("Upcoming", id="saved-upcoming")
        yield DataTable(id="tasks-table", cursor_type="row")

    def on_mount(self) -> None:
        self.load_tasks()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "saved-all":
            self._saved_filter = "all"
        elif bid == "saved-due-today":
            self._saved_filter = "due_today"
        elif bid == "saved-overdue":
            self._saved_filter = "overdue"
        elif bid == "saved-upcoming":
            self._saved_filter = "upcoming"
        else:
            return
        self.load_tasks()

    @on(Select.Changed)
    def on_filter_changed(self, event: Select.Changed) -> None:
        if event.select.id == "tasks-assignee":
            self._assignee_id = (event.value or "").strip() or None
        elif event.select.id == "tasks-status":
            self._status = (event.value or "").strip() or None
        self.load_tasks()

    @work(thread=True)
    def load_tasks(self) -> tuple[list[dict], dict[str, str], dict[str, str], object]:
        """Fetch tasks, user list, resolve contact names; return (tasks, user_map, contact_map, rate_limit_info)."""
        location_id = get_location_id()
        with GHLClient(get_token(), location_id) as client:
            users = users_svc.list_users(client)
            user_map = {}
            for u in users:
                uid = u.get("id") or ""
                if uid:
                    user_map[uid] = u.get("name") or u.get("email") or uid
            raw_tasks = tasks_svc.search_tasks(
                client,
                location_id,
                assignee_id=self._assignee_id,
                status=self._status,
            )
            tasks_filtered = _apply_date_filter(raw_tasks, self._saved_filter)
            contact_map = {}
            for t in tasks_filtered:
                if t.get("contactName"):
                    continue
                cid = t.get("contactId")
                if cid and cid not in contact_map:
                    try:
                        contact = contact_svc.get_contact(client, cid)
                        name = (
                            (contact.get("firstName") or "")
                            + " "
                            + (contact.get("lastName") or "")
                        ).strip()
                        name = name or contact.get("name") or contact.get("email") or cid
                        contact_map[cid] = name[:50]
                    except Exception:
                        contact_map[cid] = cid[:20]
            rli = client.rate_limit_info
            return (tasks_filtered, user_map, contact_map, rli)

    def _refresh_table(self) -> None:
        table = self.query_one("#tasks-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Status", "Title", "Description", "Contact", "Assignee", "Due Date")
        for t in self._tasks:
            completed = t.get("completed", False)
            status_cell = "✓" if completed else "○"
            title = (t.get("title") or "").strip() or "—"
            body = (t.get("body") or "").strip()
            desc = (body.replace("\n", " ")[:40] + "…") if len(body) > 40 else body or "—"
            contact_id = t.get("contactId") or ""
            contact_name = t.get("contactName") or self._contact_name_map.get(contact_id, contact_id[:20] if contact_id else "—")
            assignee_id = t.get("assignedTo") or ""
            assignee_name = t.get("assigneeName") or self._user_name_map.get(assignee_id, assignee_id[:20] if assignee_id else "—")
            due = format_task_date(t.get("dueDate"))
            table.add_row(status_cell, title, desc, contact_name, assignee_name, due, key=t.get("id"))

    def _get_selected_task(self) -> Optional[dict]:
        table = self.query_one("#tasks-table", DataTable)
        try:
            idx = table.cursor_row
        except Exception:
            return None
        if 0 <= idx < len(self._tasks):
            return self._tasks[idx]
        return None

    def action_refresh_tasks(self) -> None:
        self.load_tasks()

    @work(thread=True)
    def _toggle_task_complete(
        self, contact_id: str, task_id: str, completed: bool
    ) -> str:
        """Worker: update task completed state. Returns 'toggle_done' on success."""
        with GHLClient(get_token(), get_location_id()) as client:
            contact_svc.update_task_completed(client, contact_id, task_id, completed)
        return "toggle_done"

    def action_toggle_complete(self) -> None:
        task = self._get_selected_task()
        if not task:
            self.notify("Select a task first", severity="warning")
            return
        contact_id = task.get("contactId")
        task_id = task.get("id")
        if not contact_id or not task_id:
            return
        completed = not task.get("completed", False)
        self._toggle_task_complete(contact_id, task_id, completed)

    def action_edit_task(self) -> None:
        """Open the contact tasks modal for the selected task (edit completion, delete, etc.)."""
        task = self._get_selected_task()
        if not task:
            self.notify("Select a task first", severity="warning")
            return
        contact_id = task.get("contactId")
        task_id = task.get("id")
        if not contact_id or not task_id:
            return
        contact_name = task.get("contactName") or self._contact_name_map.get(contact_id) or None

        def on_done(_: object) -> None:
            self.load_tasks()

        self.app.push_screen(
            ContactTasksModal(
                contact_id,
                contact_name=contact_name,
                initial_task_id=task_id,
            ),
            on_done,
        )

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state != WorkerState.SUCCESS or not event.worker.result:
            return
        result = event.worker.result
        # Refresh table after toggle complete
        if result == "toggle_done":
            self.notify("Task updated")
            self.load_tasks()
            return
        if not isinstance(result, tuple) or len(result) != 4:
            return
        tasks_list, user_map, contact_map, rli = result
        try:
            header = self.screen.query_one("#header_bar")
            header.update_rate_limit(rli)
        except Exception:
            pass
        self._user_name_map = user_map
        self._contact_name_map = contact_map
        self._tasks = tasks_list
        self._refresh_table()
        # Populate Assignee Select with users on first load
        if not self._users and user_map:
            self._users = [{"id": k, "name": v} for k, v in user_map.items()]
            try:
                sel = self.query_one("#tasks-assignee", Select)
                opts = [("Any", "")]
                for uid, name in user_map.items():
                    opts.append((name[:40], uid))
                sel.set_options(opts)
            except Exception:
                pass
