"""Run execution logic."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from gmle.app.config.loader import load_config
from gmle.app.infra.errors import GMLEError
from gmle.app.infra.logger import get_logger, log_exception
from gmle.app.phase.runner import run as run_phases


def execute_run(
    space_id: str,
    run_id: str,
    mode: str,
    status_store: Dict[str, Dict[str, Any]],
) -> None:
    """Execute run in background."""
    logger = get_logger(space_id=space_id)
    
    try:
        status_store[run_id]["status"] = "running"
        options = {"mode": mode}
        
        logger.info("Starting run execution", extra={
            "extra_fields": {
                "run_id": run_id,
                "space_id": space_id,
                "mode": mode,
            }
        })
        
        # Track current phase in context (if runner supports it)
        # For now, we'll extract phase info from error messages if available
        run_phases(space_id, options)

        # Get final status from context
        config = load_config({"space": space_id})
        today_count = len(config.get("today_note_ids", []))
        new_accepted = len(config.get("new_source_ids", []))

        status_store[run_id].update({
            "status": "completed",
            "today_count": today_count,
            "new_accepted": new_accepted,
            "completed_at": datetime.now().isoformat(),
        })
        
        logger.info("Run completed successfully", extra={
            "extra_fields": {
                "run_id": run_id,
                "today_count": today_count,
                "new_accepted": new_accepted,
            }
        })
        
    except GMLEError as exc:
        # Use structured error information
        error_code = exc.code
        error_message = exc.user_message or str(exc)
        
        # Try to extract phase number from error message or details
        error_phase = None
        if "phase" in error_message.lower():
            import re
            phase_match = re.search(r"phase\s*(\d+)", error_message.lower())
            if phase_match:
                try:
                    error_phase = int(phase_match.group(1))
                except ValueError:
                    pass
        
        # Also check details dict for phase info
        if error_phase is None and isinstance(exc.details, dict):
            error_phase = exc.details.get("phase")
        
        log_exception(
            logger,
            "Run failed",
            exc,
            run_id=run_id,
            space_id=space_id,
            error_code=error_code,
            error_phase=error_phase,
        )
        
        status_store[run_id].update({
            "status": "failed",
            "error_message": error_message,
            "error_code": error_code,
            "error_phase": error_phase,
            "completed_at": datetime.now().isoformat(),
        })
    except Exception as exc:
        # Catch-all for unexpected errors
        log_exception(
            logger,
            "Run failed with unexpected error",
            exc,
            run_id=run_id,
            space_id=space_id,
        )
        
        status_store[run_id].update({
            "status": "failed",
            "error_message": str(exc),
            "error_code": "UNKNOWN_ERROR",
            "error_phase": None,
            "completed_at": datetime.now().isoformat(),
        })

