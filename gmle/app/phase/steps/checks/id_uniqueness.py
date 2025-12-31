"""ID uniqueness check (I7)."""

from __future__ import annotations

from typing import Dict, List

from gmle.app.adapters.anki_client import notes_info
from gmle.app.infra.errors import AnkiError


def check_id_uniqueness(note_ids: List[int]) -> None:
    """Check ID uniqueness (I7)."""
    if not note_ids:
        return
    try:
        notes = notes_info(note_ids)
        id_tags: Dict[str, List[int]] = {}
        for note in notes:
            tags = note.get("tags", [])
            for tag in tags:
                if tag.startswith("id::"):
                    id_val = tag[4:]
                    if id_val not in id_tags:
                        id_tags[id_val] = []
                    id_tags[id_val].append(note["noteId"])
        duplicates = {k: v for k, v in id_tags.items() if len(v) > 1}
        if duplicates:
            raise AnkiError(f"duplicate ID tags: {duplicates}")
    except Exception as exc:
        if isinstance(exc, AnkiError):
            raise
        raise AnkiError("ID一意検証失敗") from exc
