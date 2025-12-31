"""FallbackPool: 残り全部."""

from __future__ import annotations

from typing import Any, Dict, List


def select_fallback_pool(
    base_notes: List[Dict[str, Any]],
    exclude_note_ids: set[int],
) -> List[int]:
    """Select FallbackPool: remaining all."""
    return [n["noteId"] for n in base_notes if n["noteId"] not in exclude_note_ids]
