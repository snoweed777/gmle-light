"""Fetch BASE notes."""

from __future__ import annotations

from typing import Any, Dict, List

from gmle.app.adapters.anki_client import build_base_query, find_notes, notes_info
from gmle.app.infra.errors import AnkiError
from gmle.app.infra.logger import get_logger, log_exception


def fetch_base_notes(deck_bank: str, config: Dict[str, Any] | None = None) -> List[int]:
    """Retrieve BASE note IDs."""
    space_id = config.get("space_id") if config else None
    logger = get_logger(space_id=space_id)
    
    query = build_base_query(deck_bank, config=config)
    try:
        logger.debug("Fetching BASE notes", extra={
            "extra_fields": {
                "deck_bank": deck_bank,
                "query": query,
            }
        })
        note_ids = find_notes(query)
        logger.debug("BASE notes fetched", extra={
            "extra_fields": {
                "note_count": len(note_ids),
            }
        })
        return note_ids
    except AnkiError:
        raise
    except Exception as exc:
        log_exception(
            logger,
            "BASE fetch failed",
            exc,
            deck_bank=deck_bank,
            query=query,
        )
        raise AnkiError(
            f"BASE fetch failed: {query}",
            code="BASE_FETCH_FAILED",
            user_message=f"BASEノートの取得に失敗しました: {deck_bank}",
            details={"query": query, "deck_bank": deck_bank},
        ) from exc


def fetch_base_notes_info(deck_bank: str, config: Dict[str, Any] | None = None) -> List[dict]:
    """Retrieve BASE notes with info."""
    space_id = config.get("space_id") if config else None
    logger = get_logger(space_id=space_id)
    
    note_ids = fetch_base_notes(deck_bank, config=config)
    if not note_ids:
        logger.debug("No BASE notes found")
        return []
    
    logger.debug("Fetching BASE notes info", extra={
        "extra_fields": {"note_count": len(note_ids)}
    })
    notes = notes_info(note_ids)
    logger.debug("BASE notes info fetched", extra={
        "extra_fields": {"note_count": len(notes)}
    })
    return notes
