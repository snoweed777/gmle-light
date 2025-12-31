"""Ingest writer (spec 21.1)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from gmle.app.infra.jsonio import atomic_write_json
from gmle.app.infra.jsonl_io import append_jsonl, get_jsonl_ids


def write_queue(queue_path: Path, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Write to queue.jsonl (append-only, immutable)."""
    existing_ids = get_jsonl_ids(queue_path, id_key="source_id")
    new_sources = [s for s in sources if s["source_id"] not in existing_ids]
    
    for source in new_sources:
        append_jsonl(queue_path, source)
    
    return new_sources


def write_quarantine(quarantine_path: Path, sources: List[Dict[str, Any]]) -> None:
    """Write to quarantine.jsonl (append-only)."""
    for source in sources:
        append_jsonl(quarantine_path, source)


def write_ingest_log(log_dir: Path, date_str: str, payload: Dict[str, Any]) -> Path:
    """Write ingest log."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{date_str}.json"
    atomic_write_json(log_path, payload)
    return log_path
