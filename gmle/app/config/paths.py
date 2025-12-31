"""Path resolution."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def resolve_paths(root: Path, space_id: str, cfg: Dict[str, Any]) -> Dict[str, Path]:
    """Resolve key paths for a given space."""
    data_root = Path(cfg.get("data_root") or f"data/{space_id}")
    sources_root = Path(cfg.get("sources_root") or f"sources/{space_id}")

    paths = {
        "data_root": root / data_root,
        "sources_root": root / sources_root,
        "items": root / data_root / "items.json",
        "ledger": root / data_root / "used_source_ids.jsonl",
        "lock": root / data_root / "gmle.lock",
        "runlog_dir": root / data_root / "runs",
        "queue": root / sources_root / "queue.jsonl",
        "quarantine": root / sources_root / "quarantine.jsonl",
        "ingest_log_dir": root / sources_root / "ingest_log",
    }
    return paths
