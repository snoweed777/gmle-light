"""Queue I/O (immutable append-only)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import orjson


def read_queue(queue_path: Path) -> List[Dict[str, Any]]:
    """Read queue.jsonl (immutable, read-only)."""
    if not queue_path.exists():
        return []
    sources = []
    with queue_path.open("rb") as f:
        for line in f:
            if line.strip():
                sources.append(orjson.loads(line))
    return sources
