"""Run execution logic."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from gmle.app.config.loader import load_config
from gmle.app.infra.errors import AnkiError, ConfigError, InfraError, SOTError
from gmle.app.phase.runner import run as run_phases


def _get_error_code(exc: Exception) -> str:
    """Get error code from exception."""
    if isinstance(exc, AnkiError):
        return "ANKI_ERROR"
    elif isinstance(exc, ConfigError):
        return "CONFIG_ERROR"
    elif isinstance(exc, SOTError):
        return "SOT_ERROR"
    elif isinstance(exc, InfraError):
        error_msg = str(exc).lower()
        if "429" in error_msg or "rate limit" in error_msg or "too many requests" in error_msg:
            return "RATE_LIMIT"
        return "INFRA_ERROR"
    else:
        return "UNKNOWN_ERROR"


def execute_run(
    space_id: str,
    run_id: str,
    mode: str,
    status_store: Dict[str, Dict[str, Any]],
) -> None:
    """Execute run in background."""
    try:
        status_store[run_id]["status"] = "running"
        options = {"mode": mode}
        
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
    except (AnkiError, ConfigError, InfraError, SOTError) as exc:
        error_code = _get_error_code(exc)
        error_message = str(exc)
        
        # Try to extract phase number from error message
        error_phase = None
        if "phase" in error_message.lower():
            # Look for "phase X" pattern
            import re
            phase_match = re.search(r"phase\s*(\d+)", error_message.lower())
            if phase_match:
                try:
                    error_phase = int(phase_match.group(1))
                except ValueError:
                    pass
        
        status_store[run_id].update({
            "status": "failed",
            "error_message": error_message,
            "error_code": error_code,
            "error_phase": error_phase,
            "completed_at": datetime.now().isoformat(),
        })
    except Exception as exc:
        # Catch-all for unexpected errors
        status_store[run_id].update({
            "status": "failed",
            "error_message": str(exc),
            "error_code": "UNKNOWN_ERROR",
            "error_phase": None,
            "completed_at": datetime.now().isoformat(),
        })

