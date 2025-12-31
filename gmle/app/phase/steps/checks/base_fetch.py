"""BASE fetch check."""

from __future__ import annotations

from typing import List

from gmle.app.adapters.anki_client import build_base_query, find_notes
from gmle.app.infra.errors import AnkiError


def check_base_fetch(deck_bank: str) -> List[int]:
    """Check BASE fetch capability."""
    query = build_base_query(deck_bank)
    try:
        return find_notes(query)
    except Exception as exc:
        raise AnkiError(f"BASE fetch failed: {query}") from exc
