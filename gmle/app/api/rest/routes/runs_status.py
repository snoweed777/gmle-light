"""Run status management."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from gmle.app.api.rest.errors import raise_not_found
from gmle.app.api.rest.models import RunResponse
from gmle.app.config.loader import load_config
from gmle.app.infra.time_id import datestamp_and_run_id


def load_run_from_runlog(space_id: str, run_id: str) -> RunResponse:
    """Load run status from runlog file."""
    config = load_config({"space": space_id})
    runlog_dir = Path(config["paths"].get("runlog_dir", config["paths"]["data_root"] / "runs"))
    date_str, _ = datestamp_and_run_id()
    runlog_path = runlog_dir / date_str / f"{run_id}.json"

    if not runlog_path.exists():
        raise_not_found("Run", run_id)

    with runlog_path.open() as f:
        data = json.load(f)

    return RunResponse(
        run_id=run_id,
        space_id=space_id,
        mode=data.get("mode", "normal"),
        status=data.get("status", "completed"),
        today_count=data.get("today_count"),
        new_accepted=data.get("new_accepted"),
        degraded=data.get("degraded", False),
        degraded_reason=data.get("degraded_reason"),
        error_message=data.get("error_message"),
        error_code=data.get("error_code"),
        error_phase=data.get("error_phase"),
        started_at=datetime.fromisoformat(
            data.get("started_at", datetime.now().isoformat())
        ),
        completed_at=datetime.fromisoformat(
            data.get("completed_at", datetime.now().isoformat())
        ),
    )


def get_run_status(
    space_id: str,
    run_id: str,
    status_store: Dict[str, Dict[str, Any]],
) -> RunResponse:
    """Get run status from memory or runlog."""
    if run_id not in status_store:
        return load_run_from_runlog(space_id, run_id)

    status_data = status_store[run_id]
    return RunResponse(
        run_id=run_id,
        space_id=space_id,
        mode=status_data["mode"],
        status=status_data["status"],
        today_count=status_data.get("today_count"),
        new_accepted=status_data.get("new_accepted"),
        degraded=status_data.get("degraded", False),
        degraded_reason=status_data.get("degraded_reason"),
        error_message=status_data.get("error_message"),
        error_code=status_data.get("error_code"),
        error_phase=status_data.get("error_phase"),
        started_at=datetime.fromisoformat(status_data["started_at"]),
        completed_at=(
            datetime.fromisoformat(str(status_data.get("completed_at")))
            if status_data.get("completed_at")
            else None
        ),
    )

