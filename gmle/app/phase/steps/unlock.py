"""Phase 10: Unlock."""

from __future__ import annotations

from typing import Any, Dict

from gmle.app.infra.lock import release_lock


def execute(context: Dict[str, Any]) -> None:
    """Release lock (Phase 10)."""
    paths = context["paths"]
    release_lock(paths["lock"])
