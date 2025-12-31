"""Select degraded Today (simple selection)."""

from __future__ import annotations

from typing import Any, Dict, List


def select_degraded_today(base_notes: List[Dict[str, Any]], target_total: int) -> List[int]:
    """Select degraded Today (simple: first N active notes)."""
    active_notes = [n for n in base_notes if "status::retired" not in n.get("tags", [])]
    return [n["noteId"] for n in active_notes[:target_total]]
