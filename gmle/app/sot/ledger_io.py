"""Ledger I/O (append-only)."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import orjson


def append_ledger(path: Path, record: Dict[str, str]) -> None:
    """Append ledger record (append-only)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as f:
        f.write(orjson.dumps(record) + b"\n")


def read_ledger(path: Path) -> list[Dict[str, str]]:
    """Read all ledger records."""
    if not path.exists():
        return []
    records = []
    with path.open("rb") as f:
        for line in f:
            if line.strip():
                records.append(orjson.loads(line))
    return records
