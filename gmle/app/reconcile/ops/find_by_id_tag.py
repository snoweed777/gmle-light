"""Find note by id tag."""

from __future__ import annotations

from typing import List

from gmle.app.adapters.anki_client import find_notes


def find_note_by_id_tag(item_id: str) -> List[int]:
    """Find note IDs by id tag (spec 7)."""
    query = f'tag:id::{item_id}'
    return find_notes(query)
