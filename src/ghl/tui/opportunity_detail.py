"""Opportunity detail modal with stage display and move."""

from __future__ import annotations

from typing import Optional

from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..services import pipelines as pipeline_svc
from ..services.opportunities import get_opportunity
from .opportunity_move import MoveStageModal


def _contact_display(opp: dict) -> str:
    """Contact name or email for display."""
    contact = opp.get("contact") or {}
    return contact.get("name") or contact.get("email") or "—"


def _stage_label(opp: dict, stages: Optional[list[dict]] = None) -> str:
    """Stage name if available, else stage ID."""
    name = opp.get("pipelineStageName")
    if name:
        return name
    sid = opp.get("pipelineStageId")
    if stages and sid:
        for s in stages:
            if s.get("id") == sid:
                return s.get("name", sid)
    return sid or "—"


class OpportunityDetailModal(ModalScreen[None]):
    """Show opportunity details."""

    def __init__(self, opportunity_id: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._opportunity_id = opportunity_id
        self._opp: Optional[dict] = None

    def compose(self):
        with Vertical():
            yield Static("Loading…", id="opp-detail")
            yield Button("Move stage", id="opp-move")
            yield Button("Close", id="opp-close")

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        with GHLClient(get_token(), get_location_id()) as client:
            self._opp = get_opportunity(client, self._opportunity_id)
        opp = self._opp
        stages: Optional[list[dict]] = None
        if opp.get("pipelineId"):
            with GHLClient(get_token(), get_location_id()) as client:
                pipelines = pipeline_svc.list_pipelines(client)
            pipeline = next((p for p in pipelines if p.get("id") == opp.get("pipelineId")), None)
            if pipeline:
                stages = pipeline.get("stages", [])
        lines = [
            f"[bold]{opp.get('name') or '—'}[/bold]",
            f"Value: {opp.get('monetaryValue')}",
            f"Status: {opp.get('status')}",
            f"Contact: {_contact_display(opp)}",
            f"Stage: {_stage_label(opp, stages)}",
        ]
        self.query_one("#opp-detail", Static).update("\n".join(lines))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "opp-close":
            self.dismiss(None)
            return
        if event.button.id == "opp-move":
            self._do_move()

    def _do_move(self) -> None:
        if not self._opp:
            return
        pipeline_id = self._opp.get("pipelineId")
        if not pipeline_id:
            self.notify("No pipeline for this opportunity", severity="warning")
            return
        with GHLClient(get_token(), get_location_id()) as client:
            pipelines = pipeline_svc.list_pipelines(client)
        pipeline = next((p for p in pipelines if p.get("id") == pipeline_id), None)
        if not pipeline:
            self.notify("Pipeline not found", severity="warning")
            return
        stages = pipeline.get("stages", [])
        if not stages:
            self.notify("No stages in pipeline", severity="warning")
            return
        stage_ids = [s["id"] for s in stages]
        stage_names = [s.get("name", s["id"]) for s in stages]
        current_stage_id = self._opp.get("pipelineStageId")

        def on_done(_: None) -> None:
            self._refresh()

        self.app.push_screen(
            MoveStageModal(
                self._opportunity_id,
                stage_ids,
                stage_names,
                current_stage_id=current_stage_id,
            ),
            on_done,
        )
