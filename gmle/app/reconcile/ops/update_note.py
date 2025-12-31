"""Update note fields."""

from __future__ import annotations

from typing import Any, Dict

from gmle.app.adapters.anki_client import invoke, notes_info
from gmle.app.infra.errors import AnkiError
from .add_note import _build_fields, _build_tags


def update_note(note_id: int, item: Dict[str, Any]) -> None:
    """Update note fields (spec 16.2: updateNoteFieldsで全上書き)."""
    fields = _build_fields(item)
    tags = _build_tags(item)
    try:
        # AnkiConnect API format: note parameter should be a dict with id and fields
        invoke("updateNoteFields", {"note": {"id": note_id, "fields": fields}})
        # Remove all existing tags and add new ones
        # First, get current tags to remove them
        current_note_info = notes_info([note_id])
        if current_note_info and len(current_note_info) > 0:
            current_tags = current_note_info[0].get("tags", [])
            # Remove all current tags
            for tag in current_tags:
                invoke("removeTags", {"notes": [note_id], "tags": tag})
        # Add new tags
        for tag in tags:
            invoke("addTags", {"notes": [note_id], "tags": tag})
    except Exception as exc:
        raise AnkiError(f"updateNote failed: note_id={note_id}, item_id={item.get('id', 'unknown')}") from exc
