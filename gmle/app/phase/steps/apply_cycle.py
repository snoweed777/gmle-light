"""Phase 7: Apply Cycle."""

from __future__ import annotations

from typing import Any, Dict

from gmle.app.cycle.cycle_apply import cleanup_cycle_tags, apply_today_tags
from gmle.app.infra.time_id import today_str


def execute(context: Dict[str, Any]) -> None:
    """Apply cycle (Phase 7)."""
    base_note_ids = context["base_note_ids"]
    today_note_ids = context["today_note_ids"]
    today_tag = f"cycle::{today_str()}"

    cleanup_cycle_tags(base_note_ids)
    apply_today_tags(today_note_ids, today_tag)
