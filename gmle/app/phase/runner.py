"""Phase runner (spec 11.1)."""

from __future__ import annotations

import time
from typing import Any, Dict

from gmle.app.config.loader import load_config
from gmle.app.degrade.handler import handle_degrade
from gmle.app.infra.errors import AnkiError, ConfigError, InfraError, SOTError
from gmle.app.infra.logger import get_logger, log_exception
from gmle.app.infra.time_id import datestamp_and_run_id
from gmle.app.reconcile.sync import reconcile
from .steps.apply_cycle import execute as apply_cycle
from .steps.commit import execute as commit
from .steps.generate_new import execute as generate_new
from .steps.load import execute as load
from .steps.lock import execute as lock_step
from .steps.plan import execute as plan
from .steps.select_today import execute as select_today
from .steps.selfcheck_end import execute as selfcheck_end
from .steps.selfcheck_start import execute as selfcheck_start
from .steps.unlock import execute as unlock


PHASE_NAMES = {
    0: "lock",
    1: "selfcheck_start",
    2: "load",
    3: "plan",
    4: "generate_new",
    5: "reconcile",
    6: "select_today",
    7: "apply_cycle",
    8: "commit",
    9: "selfcheck_end",
    10: "unlock",
}


def run(space_id: str, options: Dict[str, Any] | None = None) -> None:
    """Execute phases 0-10 (spec 11.1)."""
    options = options or {}
    context = load_config({"space": space_id, **options})
    logger = get_logger(space_id=space_id)
    
    date_str, run_id = datestamp_and_run_id()
    context["run_id"] = run_id
    context["today_str"] = date_str
    context["mode"] = options.get("mode", "normal")
    context["degraded"] = False
    context["new_source_ids"] = []
    context["selfcheck_passed"] = False
    
    logger.info("Starting GMLE+ run", extra={"extra_fields": {
        "run_id": run_id,
        "space_id": space_id,
        "mode": context["mode"],
    }})

    try:
        # Phase 0: Lock
        _execute_phase(logger, 0, "lock", lock_step, context)
        
        # Phase 1: Selfcheck Start
        _execute_phase(logger, 1, "selfcheck_start", selfcheck_start, context)
        context["selfcheck_passed"] = True
        
        # Phase 2: Load
        _execute_phase(logger, 2, "load", load, context)
        
        # Phase 3: Plan
        _execute_phase(logger, 3, "plan", plan, context)
        
        # Phase 4: Generate New
        _execute_phase(logger, 4, "generate_new", generate_new, context)
        
        # Phase 5: Reconcile (skip in batch mode)
        if context["mode"] != "batch":
            _execute_phase(logger, 5, "reconcile", lambda ctx: reconcile(ctx["items"], ctx["deck_bank"], config=ctx), context)
            
            # Reload base_notes and base_cards after reconcile to include newly added MCQs
            from gmle.app.adapters.anki_client import cards_info
            from gmle.app.cycle.base_fetch import fetch_base_notes_info
            
            base_notes = fetch_base_notes_info(context["deck_bank"])
            base_note_ids = [n["noteId"] for n in base_notes]
            base_cards = []
            if base_note_ids:
                card_ids = []
                for note in base_notes:
                    card_ids.extend(note.get("cards", []))
                if card_ids:
                    base_cards = cards_info(card_ids)
            
            context["base_notes"] = base_notes
            context["base_note_ids"] = base_note_ids
            context["base_cards"] = base_cards
        
        # Phase 6-9: Only if selfcheck passed
        if context["selfcheck_passed"]:
            # Phase 6: Select Today
            _execute_phase(logger, 6, "select_today", select_today, context)
            
            # Phase 7: Apply Cycle
            _execute_phase(logger, 7, "apply_cycle", apply_cycle, context)
            
            # Phase 8: Commit
            _execute_phase(logger, 8, "commit", commit, context)
            
            # Phase 9: Selfcheck End
            _execute_phase(logger, 9, "selfcheck_end", selfcheck_end, context)
        
        logger.info("GMLE+ run completed successfully", extra={"extra_fields": {
            "run_id": run_id,
            "space_id": space_id,
            "today_count": len(context.get("today_note_ids", [])),
            "new_accepted": len(context.get("new_source_ids", [])),
        }})
        
    except (AnkiError, ConfigError, InfraError, SOTError) as exc:
        context["degraded"] = True
        context["degraded_reason"] = str(exc)
        
        if not context["selfcheck_passed"]:
            log_exception(
                logger,
                "Selfcheck failed, skipping destructive operations",
                exc,
                run_id=run_id,
                space_id=space_id,
                phase="selfcheck_start",
            )
        else:
            log_exception(
                logger,
                "Error during execution, entering Safe-Degrade mode",
                exc,
                run_id=run_id,
                space_id=space_id,
            )
            handle_degrade(str(exc), context)
    finally:
        # Phase 10: Unlock
        try:
            _execute_phase(logger, 10, "unlock", unlock, context)
        except Exception as exc:
            log_exception(
                logger,
                "Error during unlock phase",
                exc,
                run_id=run_id,
                space_id=space_id,
                phase="unlock",
            )


def _execute_phase(
    logger: Any,
    phase_num: int,
    phase_name: str,
    phase_func: Any,
    context: Dict[str, Any],
) -> None:
    """Execute a phase with logging."""
    logger.debug(f"Phase {phase_num} ({phase_name}) started", extra={"extra_fields": {
        "phase": phase_num,
        "phase_name": phase_name,
    }})
    
    start_time = time.time()
    try:
        phase_func(context)
        elapsed = time.time() - start_time
        
        logger.info(f"Phase {phase_num} ({phase_name}) completed", extra={"extra_fields": {
            "phase": phase_num,
            "phase_name": phase_name,
            "elapsed_seconds": round(elapsed, 3),
        }})
    except Exception as exc:
        elapsed = time.time() - start_time
        log_exception(
            logger,
            f"Phase {phase_num} ({phase_name}) failed",
            exc,
            phase=phase_num,
            phase_name=phase_name,
            elapsed_seconds=round(elapsed, 3),
        )
        raise
