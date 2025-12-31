"""Runlog writer."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .jsonio import atomic_write_json
from .time_id import today_str


def write_runlog(runlog_dir: Path, run_id: str, payload: Dict[str, Any]) -> Path:
    """Write runlog file."""
    date_dir = runlog_dir / today_str()
    date_dir.mkdir(parents=True, exist_ok=True)
    path = date_dir / f"{run_id}.json"
    atomic_write_json(path, payload)
    return path
