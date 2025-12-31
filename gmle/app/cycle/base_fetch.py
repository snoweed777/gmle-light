"""Fetch BASE notes."""

from __future__ import annotations

from typing import Any, Dict, List

from gmle.app.adapters.anki_client import build_base_query, find_notes, notes_info
from gmle.app.infra.errors import AnkiError


def fetch_base_notes(deck_bank: str, config: Dict[str, Any] | None = None) -> List[int]:
    """Retrieve BASE note IDs."""
    query = build_base_query(deck_bank, config=config)
    try:
        return find_notes(query)
    except Exception as exc:
        raise AnkiError(f"BASE fetch failed: {query}") from exc


def fetch_base_notes_info(deck_bank: str, config: Dict[str, Any] | None = None) -> List[dict]:
    """Retrieve BASE notes with info."""
    note_ids = fetch_base_notes(deck_bank, config=config)
    if not note_ids:
        return []
    return notes_info(note_ids)
