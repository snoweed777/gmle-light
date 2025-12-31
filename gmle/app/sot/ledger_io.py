"""Ledger I/O (append-only)."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from gmle.app.infra.jsonl_io import append_jsonl, read_jsonl


def append_ledger(path: Path, record: Dict[str, str]) -> None:
    """Append ledger record (append-only)."""
    append_jsonl(path, record)


def read_ledger(path: Path) -> list[Dict[str, str]]:
    """Read all ledger records."""
    return read_jsonl(path)
