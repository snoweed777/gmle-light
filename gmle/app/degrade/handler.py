"""Safe-Degrade handler (spec 12.2)."""

from __future__ import annotations

from typing import Any, Dict

from gmle.app.adapters.anki_client import build_base_query
from gmle.app.cycle.cycle_apply import cleanup_cycle_tags, apply_today_tags
from gmle.app.cycle.base_fetch import fetch_base_notes_info
from gmle.app.infra.logger import get_logger, with_fields
from gmle.app.infra.time_id import today_str
from .check_minimal_cycle import check_minimal_cycle_conditions
from .select_degraded_today import select_degraded_today


def get_logger_for_context(context: dict) -> Any:
    """Get logger with space_id from context."""
    return get_logger(space_id=context.get("space_id"))


def handle_degrade(reason: str, context: Dict[str, Any]) -> None:
    """Handle Safe-Degrade path (spec 12.2)."""
    logger = get_logger_for_context(context)
    deck_bank = context["deck_bank"]
    params = context.get("params", {})
    total = params.get("total", 30)

    logger.warning("Safe-Degrade mode", **with_fields(logger, reason=reason, run_id=context.get("run_id")))

    can_cycle, base_note_ids, cycle_error = check_minimal_cycle_conditions(deck_bank, config=context)
    if not can_cycle:
        query = build_base_query(deck_bank, config=context)
        logger.error("Cannot perform degraded cycle", **with_fields(logger, error=cycle_error, query=query, run_id=context.get("run_id")))
        return

    base_notes = fetch_base_notes_info(deck_bank, config=context)
    today_note_ids = select_degraded_today(base_notes, total)
    if len(today_note_ids) < total:
        query = build_base_query(deck_bank, config=context)
        logger.error("Insufficient notes for degraded cycle", **with_fields(logger, available=len(today_note_ids), required=total, query=query, run_id=context.get("run_id")))
        return

    cleanup_cycle_tags(base_note_ids)
    today_tag = f"cycle::{today_str()}"
    apply_today_tags(today_note_ids, today_tag)
    logger.info("Degraded cycle applied", **with_fields(logger, today_count=len(today_note_ids), run_id=context.get("run_id")))
