"""SOT items I/O."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Dict

from gmle.app.infra.jsonio import read_json, atomic_write_json


def read_items(path: Path) -> List[Dict[str, Any]]:
    """Read items.json."""
    if not path.exists():
        return []
    data = read_json(path)
    if not isinstance(data, list):
        raise ValueError(f"items.json must be a list, got {type(data)}")
    return data


def write_items(path: Path, items: List[Dict[str, Any]]) -> None:
    """Write items.json atomically."""
    atomic_write_json(path, items)
