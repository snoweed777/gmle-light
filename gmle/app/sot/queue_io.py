"""Queue I/O (immutable append-only)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from gmle.app.infra.jsonl_io import read_jsonl


def read_queue(queue_path: Path) -> List[Dict[str, Any]]:
    """Read queue.jsonl (immutable, read-only)."""
    return read_jsonl(queue_path)
