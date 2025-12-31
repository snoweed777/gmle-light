"""Reconcile SOT to Anki (spec 16.2)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Set

from gmle.app.adapters.anki_client import build_base_query, find_notes, sync as anki_sync
from .ops.add_note import add_note
from .ops.find_by_id_tag import find_note_by_id_tag
from .ops.mark_orphan import mark_orphan
from .ops.update_note import update_note

logger = logging.getLogger(__name__)

NOTE_TYPE = "GMLE_MCQA"


def reconcile(items: List[Dict[str, Any]], deck_bank: str, base_query: str | None = None, config: Dict[str, Any] | None = None) -> None:
    """Sync items into Anki (spec 16.2)."""
    if base_query is None:
        base_query = build_base_query(deck_bank, config=config)
    base_note_ids = set(find_notes(base_query))
    processed_note_ids: Set[int] = set()

    for item in items:
        item_id = item["id"]
        note_ids = find_note_by_id_tag(item_id)
        if not note_ids:
            note_id = add_note(item, deck_bank, NOTE_TYPE)
            processed_note_ids.add(note_id)
        else:
            note_id = note_ids[0]
            update_note(note_id, item)
            processed_note_ids.add(note_id)

    orphan_note_ids = list(base_note_ids - processed_note_ids)
    if orphan_note_ids:
        mark_orphan(orphan_note_ids)
    
    # Sync to AnkiWeb after reconciliation (data protection)
    try:
        anki_sync(config=config)
        logger.info("AnkiWeb sync completed after reconciliation")
    except Exception as e:
        logger.warning(f"AnkiWeb sync failed after reconciliation: {e}")
