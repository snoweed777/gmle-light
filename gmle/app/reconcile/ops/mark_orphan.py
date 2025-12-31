"""Mark orphan notes."""

from __future__ import annotations

from typing import List

from gmle.app.adapters.anki_client import invoke
from gmle.app.infra.errors import AnkiError


def mark_orphan(note_ids: List[int]) -> None:
    """Mark orphan notes (spec 16.2: status::orphan付与)."""
    if not note_ids:
        return
    try:
        invoke("addTags", {"notes": note_ids, "tags": "status::orphan"})
    except Exception as exc:
        raise AnkiError(f"mark orphan failed: {len(note_ids)} notes") from exc
