"""Pipeline board (kanban) view: stages as columns, opportunities as cards."""

from __future__ import annotations

from typing import Optional

from textual import on, work
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Button,
    Label,
    ListView,
    ListItem,
    Select,
    Static,
)


class OpportunityListView(ListView):
    """ListView for opportunities that shows Enter=View in the footer."""

    BINDINGS = [
        Binding("enter", "select_cursor", "View"),
        Binding("up", "cursor_up", "Cursor up", show=False),
        Binding("down", "cursor_down", "Cursor down", show=False),
    ]
from textual.worker import Worker, WorkerState

from ...auth import get_location_id, get_token
from ...client import GHLClient
from ...services import opportunities as opp_svc
from ...services import pipelines as pipeline_svc
from ..opportunity_detail import OpportunityDetailModal
from ..opportunity_move import MoveStageModal


def _opp_label(opp: dict) -> str:
    name = opp.get("name") or "—"
    value = opp.get("monetaryValue")
    val_s = f" ${value:,.0f}" if value is not None else ""
    contact = (opp.get("contact") or {})
    contact_name = contact.get("name") or contact.get("email") or ""
    if contact_name:
        return f"{name}{val_s}\n[dim]{contact_name[:30]}[/dim]"
    return f"{name}{val_s}"


class StageColumn(Container):
    """One column: stage name + list of opportunity cards."""

    DEFAULT_CSS = """
    StageColumn {
        width: 22;
        min-width: 22;
        height: auto;
        border: solid $primary-darken-2;
        padding: 1;
        margin: 0 1 0 0;
    }
    .stage-header {
        text-style: bold;
        padding: 0 0 1 0;
    }
    """

    def __init__(self, stage_id: str, stage_name: str, opportunities: list[dict], **kwargs) -> None:
        super().__init__(**kwargs)
        self.stage_id = stage_id
        self.stage_name = stage_name
        self.opportunities = opportunities

    def compose(self):
        yield Static(self.stage_name, classes="stage-header")
        items = [ListItem(Static(_opp_label(opp))) for opp in self.opportunities]
        yield OpportunityListView(*items, id="stage-opps")

    @on(ListView.Selected)
    def on_opportunity_selected(self, event: ListView.Selected) -> None:
        """Open opportunity detail when user presses Enter on an opportunity."""
        idx = event.index
        if 0 <= idx < len(self.opportunities):
            self.app.push_screen(OpportunityDetailModal(self.opportunities[idx]["id"]))


class PipelineBoardView(Container):
    """Pipeline board: pipeline selector + stage columns with opportunity cards."""

    BINDINGS = [
        ("m", "move_opportunity", "Move"),
        ("w", "mark_won", "Won"),
        ("l", "mark_lost", "Lost"),
    ]

    DEFAULT_CSS = """
    PipelineBoardView {
        width: 100%;
        height: auto;
        layout: vertical;
    }
    #board-toolbar {
        height: auto;
        padding: 0 0 1 0;
    }
    #board-columns {
        layout: horizontal;
        height: auto;
        overflow-x: auto;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._pipelines: list[dict] = []
        self._pipeline_id: Optional[str] = None
        self._pipeline: Optional[dict] = None
        self._stages: list[dict] = []
        self._opportunities_by_stage: dict[str, list[dict]] = {}
        self._all_opportunities: list[dict] = []
        self._selected_opp_id: Optional[str] = None
        self._selected_stage_id: Optional[str] = None

    def compose(self):
        with Vertical(id="board-toolbar"):
            yield Label("Pipeline:")
            yield Select(
                [("Select pipeline…", "")],
                id="pipeline-select",
                allow_blank=False,
            )
        yield ScrollableContainer(id="board-columns")

    def on_mount(self) -> None:
        self.load_pipelines()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "pipeline-select":
            return
        val = event.value
        if val and val != "":
            self._pipeline_id = val
            self.load_board()

    @work(thread=True)
    def load_pipelines(self) -> tuple[list[dict], object]:
        with GHLClient(get_token(), get_location_id()) as client:
            pipelines = pipeline_svc.list_pipelines(client)
            rli = client.rate_limit_info
            return (pipelines, rli)

    @work(thread=True)
    def load_board(self) -> tuple[dict, object]:
        pipeline_id = self._pipeline_id
        if not pipeline_id:
            return ({}, None)
        # Use pipeline from list (get_pipeline requires scope that often isn't granted)
        pipeline = next((p for p in self._pipelines if p.get("id") == pipeline_id), None)
        if not pipeline:
            return ({}, None)
        with GHLClient(get_token(), get_location_id()) as client:
            opps = opp_svc.list_opportunities(
                client, pipeline_id=pipeline_id, limit=100, status="open"
            )
            rli = client.rate_limit_info
            return ({"pipeline": pipeline, "opportunities": opps}, rli)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state != WorkerState.SUCCESS or not event.worker.result:
            return
        result = event.worker.result
        if not isinstance(result, tuple) or len(result) != 2:
            return
        data, rli = result
        try:
            header = self.screen.query_one("#header_bar")
            header.update_rate_limit(rli)
        except Exception:
            pass
        if isinstance(data, list):
            self._pipelines = data
            sel = self.query_one("#pipeline-select", Select)
            options = [("Select pipeline…", "")]
            for p in self._pipelines:
                options.append((p.get("name") or p.get("id", ""), p.get("id", "")))
            sel.set_options(options)
            if self._pipeline_id and any(p.get("id") == self._pipeline_id for p in self._pipelines):
                sel.value = self._pipeline_id
            return
        if isinstance(data, dict) and "pipeline" in data:
            self._pipeline = data["pipeline"]
            self._stages = self._pipeline.get("stages", [])
            opps = data.get("opportunities", [])
            # List API may not include stages; derive from opportunities if needed
            if not self._stages and opps:
                seen: dict[str, str] = {}
                for o in opps:
                    sid = o.get("pipelineStageId")
                    if sid and sid not in seen:
                        seen[sid] = o.get("pipelineStageName") or sid[:8]
                self._stages = [{"id": k, "name": v} for k, v in seen.items()]
            self._all_opportunities = opps
            by_stage: dict[str, list[dict]] = {s["id"]: [] for s in self._stages}
            for o in opps:
                sid = o.get("pipelineStageId")
                if sid and sid in by_stage:
                    by_stage[sid].append(o)
            self._opportunities_by_stage = by_stage
            self.call_later(self._render_columns)

    async def _render_columns(self) -> None:
        container = self.query_one("#board-columns", ScrollableContainer)
        await container.remove_children()
        for stage in self._stages:
            sid = stage.get("id", "")
            name = stage.get("name", "—")
            opps = self._opportunities_by_stage.get(sid, [])
            col = StageColumn(sid, name, opps, id=f"col-{sid}")
            container.mount(col)

    def _get_selected_opportunity(self) -> Optional[dict]:
        focused = self.screen.focused
        if focused is None:
            return None
        for col in self.query("StageColumn"):
            if focused in col.query("*"):
                lst = col.query_one("#stage-opps", OpportunityListView)
                idx = lst.index
                opps = getattr(col, "opportunities", [])
                if 0 <= idx < len(opps):
                    return opps[idx]
                break
        return None

    def action_move_opportunity(self) -> None:
        opp = self._get_selected_opportunity()
        if not opp:
            self.notify("Select an opportunity first", severity="warning")
            return
        stage_ids = [s["id"] for s in self._stages]
        stage_names = [s["name"] for s in self._stages]
        def on_done(_: None) -> None:
            self.load_board()
            self.set_timer(3, self.load_board, name="refresh-after-move")  # Refresh again after API propagates

        self.app.push_screen(
            MoveStageModal(opp["id"], stage_ids, stage_names, current_stage_id=opp.get("pipelineStageId")),
            on_done,
        )

    def action_mark_won(self) -> None:
        opp = self._get_selected_opportunity()
        if not opp:
            self.notify("Select an opportunity first", severity="warning")
            return
        with GHLClient(get_token(), get_location_id()) as client:
            opp_svc.mark_won(client, opp["id"])
        self.app.notify("Marked as won")
        self.load_board()

    def action_mark_lost(self) -> None:
        opp = self._get_selected_opportunity()
        if not opp:
            self.notify("Select an opportunity first", severity="warning")
            return
        with GHLClient(get_token(), get_location_id()) as client:
            opp_svc.mark_lost(client, opp["id"])
        self.app.notify("Marked as lost")
        self.load_board()
