"""Items.json parse check."""

from __future__ import annotations

from pathlib import Path

from gmle.app.infra.errors import SOTError
from gmle.app.sot.items_io import read_items


def check_items_parse(items_path: Path) -> None:
    """Check items.json parse capability."""
    if not items_path.exists():
        return
    try:
        read_items(items_path)
    except Exception as exc:
        raise SOTError(f"items.json parse failed: {items_path}") from exc
