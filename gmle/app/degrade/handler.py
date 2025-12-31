"""Safe-Degrade handler (spec 12.2)."""

from __future__ import annotations

from typing import Any, Dict

from gmle.app.adapters.anki_client import build_base_query
from gmle.app.cycle.cycle_apply import cleanup_cycle_tags, apply_today_tags
from gmle.app.cycle.base_fetch import fetch_base_notes_info
from gmle.app.infra.errors import DegradeTrigger
from gmle.app.infra.logger import get_logger, with_fields
from gmle.app.infra.time_id import today_str
from .check_minimal_cycle import check_minimal_cycle_conditions
from .select_degraded_today import select_degraded_today


def handle_degrade(reason: str, context: Dict[str, Any]) -> None:
    """Handle Safe-Degrade path (spec 12.2) with improved error handling."""
    logger = get_logger(space_id=context.get("space_id"))
    deck_bank = context["deck_bank"]
    params = context.get("params", {})
    total = params.get("total", 30)
    min_notes = params.get("degrade_min_notes", 30)

    logger.warning("Safe-Degrade mode activated", 
                   **with_fields(logger, reason=reason, run_id=context.get("run_id")))

    try:
        can_cycle, base_note_ids, cycle_error = check_minimal_cycle_conditions(
            deck_bank, min_notes=min_notes, config=context
        )
        
        if not can_cycle:
            error_msg = cycle_error or "Minimal cycle conditions not met"
            query = build_base_query(deck_bank, config=context)
            
            logger.error("Degraded cycle failed", 
                        **with_fields(logger, 
                                    error=error_msg, 
                                    query=query, 
                                    run_id=context.get("run_id")))
            
            raise DegradeTrigger(
                f"Degraded cycle failed: {error_msg}",
                code="DEGRADE_CYCLE_FAILED",
                user_message="最小限のサイクル条件を満たせませんでした",
                details={"error": error_msg, "query": query},
            )
        
        base_notes = fetch_base_notes_info(deck_bank, config=context)
        today_note_ids = select_degraded_today(base_notes, total)
        
        if len(today_note_ids) < total:
            query = build_base_query(deck_bank, config=context)
            logger.error("Insufficient notes for degraded cycle", 
                        **with_fields(logger, 
                                    available=len(today_note_ids), 
                                    required=total, 
                                    query=query, 
                                    run_id=context.get("run_id")))
            
            raise DegradeTrigger(
                f"Insufficient notes: {len(today_note_ids)}/{total}",
                code="DEGRADE_INSUFFICIENT_NOTES",
                user_message=f"十分なノートがありません（{len(today_note_ids)}/{total}）",
                details={"available": len(today_note_ids), "required": total},
            )
        
        cleanup_cycle_tags(base_note_ids)
        today_tag = f"cycle::{today_str()}"
        apply_today_tags(today_note_ids, today_tag)
        
        logger.info("Degraded cycle applied", 
                   **with_fields(logger, today_count=len(today_note_ids), run_id=context.get("run_id")))
    
    except DegradeTrigger:
        raise
    except Exception as exc:
        logger.error("Unexpected error in degrade handler", exc_info=True)
        raise DegradeTrigger(
            f"Unexpected error in degrade handler: {str(exc)}",
            code="DEGRADE_UNEXPECTED_ERROR",
            user_message="Degradeモードで予期しないエラーが発生しました",
            details={"original_error": str(exc)},
        ) from exc
