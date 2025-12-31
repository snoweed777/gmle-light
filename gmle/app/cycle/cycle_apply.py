"""Cycle cleanup and apply (spec 17)."""

from __future__ import annotations

from typing import List

from gmle.app.adapters.anki_client import invoke
from gmle.app.infra.errors import AnkiError


def cleanup_cycle_tags(note_ids: List[int]) -> None:
    """Remove cycle tags from BASE (spec 17.2)."""
    if not note_ids:
        return
    try:
        invoke("removeTags", {"notes": note_ids, "tags": "cycle"})
    except Exception as exc:
        raise AnkiError(f"cycle cleanup failed: {len(note_ids)} notes") from exc


def apply_today_tags(today_note_ids: List[int], today_tag: str) -> None:
    """Apply cycle tag to Today notes (spec 17.3)."""
    if not today_note_ids:
        return
    try:
        invoke("addTags", {"notes": today_note_ids, "tags": today_tag})
    except Exception as exc:
        raise AnkiError(f"apply today tags failed: {len(today_note_ids)} notes, tag={today_tag}") from exc
