"""Ingest writer (spec 21.1)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import orjson

from gmle.app.infra.jsonio import atomic_write_json


def write_queue(queue_path: Path, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Write to queue.jsonl (append-only, immutable)."""
    existing_ids = _get_existing_source_ids(queue_path)
    new_sources = [s for s in sources if s["source_id"] not in existing_ids]
    with queue_path.open("ab") as f:
        for source in new_sources:
            f.write(orjson.dumps(source) + b"\n")
    return new_sources


def write_quarantine(quarantine_path: Path, sources: List[Dict[str, Any]]) -> None:
    """Write to quarantine.jsonl (append-only)."""
    quarantine_path.parent.mkdir(parents=True, exist_ok=True)
    with quarantine_path.open("ab") as f:
        for source in sources:
            f.write(orjson.dumps(source) + b"\n")


def write_ingest_log(log_dir: Path, date_str: str, payload: Dict[str, Any]) -> Path:
    """Write ingest log."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{date_str}.json"
    atomic_write_json(log_path, payload)
    return log_path


def _get_existing_source_ids(queue_path: Path) -> set[str]:
    """Get existing source IDs from queue."""
    if not queue_path.exists():
        return set()
    ids = set()
    with queue_path.open("rb") as f:
        for line in f:
            if line.strip():
                data = orjson.loads(line)
                ids.add(data.get("source_id", ""))
    return ids
