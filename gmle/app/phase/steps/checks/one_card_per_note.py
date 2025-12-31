"""1ノート=1カード check."""

from __future__ import annotations

from typing import List

from gmle.app.adapters.anki_client import notes_info
from gmle.app.infra.errors import AnkiError


def check_one_card_per_note(note_ids: List[int]) -> None:
    """Check 1ノート=1カード constraint."""
    if not note_ids:
        return
    try:
        notes = notes_info(note_ids[:10])  # sample
        for note in notes:
            card_ids = note.get("cards", [])
            if len(card_ids) != 1:
                raise AnkiError(f"note {note.get('noteId')} has {len(card_ids)} cards (expected 1)")
    except Exception as exc:
        if isinstance(exc, AnkiError):
            raise
        raise AnkiError("1ノート=1カード検証失敗") from exc
