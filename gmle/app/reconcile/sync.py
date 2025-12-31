"""Reconcile SOT to Anki (spec 16.2)."""

from __future__ import annotations

from typing import Any, Dict, List, Set

from gmle.app.adapters.anki_client import build_base_query, find_notes, sync as anki_sync
from gmle.app.infra.logger import get_logger, log_exception
from .ops.add_note import add_note
from .ops.find_by_id_tag import find_note_by_id_tag
from .ops.mark_orphan import mark_orphan
from .ops.update_note import update_note

NOTE_TYPE = "GMLE_MCQA"


def reconcile(items: List[Dict[str, Any]], deck_bank: str, base_query: str | None = None, config: Dict[str, Any] | None = None) -> None:
    """Sync items into Anki (spec 16.2)."""
    space_id = config.get("space_id") if config else None
    logger = get_logger(space_id=space_id)
    
    logger.info("Starting reconciliation", extra={
        "extra_fields": {
            "item_count": len(items),
            "deck_bank": deck_bank,
        }
    })
    
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
            logger.debug("Added new note", extra={
                "extra_fields": {
                    "item_id": item_id,
                    "note_id": note_id,
                }
            })
        else:
            note_id = note_ids[0]
            update_note(note_id, item)
            processed_note_ids.add(note_id)
            logger.debug("Updated existing note", extra={
                "extra_fields": {
                    "item_id": item_id,
                    "note_id": note_id,
                }
            })

    orphan_note_ids = list(base_note_ids - processed_note_ids)
    if orphan_note_ids:
        logger.info("Marking orphan notes", extra={
            "extra_fields": {"orphan_count": len(orphan_note_ids)}
        })
        mark_orphan(orphan_note_ids)
    
    logger.info("Reconciliation completed", extra={
        "extra_fields": {
            "processed_count": len(processed_note_ids),
            "orphan_count": len(orphan_note_ids),
        }
    })
    
    # Sync to AnkiWeb after reconciliation (data protection)
    try:
        anki_sync(config=config)
        logger.info("AnkiWeb sync completed after reconciliation")
    except Exception as e:
        log_exception(
            logger,
            "AnkiWeb sync failed after reconciliation",
            e,
        )
