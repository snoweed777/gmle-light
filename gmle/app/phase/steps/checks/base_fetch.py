"""BASE fetch check."""

from __future__ import annotations

from typing import List

from gmle.app.adapters.anki_client import build_base_query, find_notes
from gmle.app.infra.errors import AnkiError
from gmle.app.infra.logger import get_logger, log_exception


def check_base_fetch(deck_bank: str) -> List[int]:
    """Check BASE fetch capability."""
    logger = get_logger()
    
    query = build_base_query(deck_bank)
    try:
        logger.debug("Checking BASE fetch capability", extra={
            "extra_fields": {
                "deck_bank": deck_bank,
                "query": query,
            }
        })
        note_ids = find_notes(query)
        logger.debug("BASE fetch check passed", extra={
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
            "BASE fetch check failed",
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
