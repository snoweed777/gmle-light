"""1ノート=1カード check."""

from __future__ import annotations

from typing import List

from gmle.app.adapters.anki_client import notes_info
from gmle.app.infra.errors import AnkiError
from gmle.app.infra.logger import get_logger, log_exception


def check_one_card_per_note(note_ids: List[int]) -> None:
    """Check 1ノート=1カード constraint."""
    logger = get_logger()
    
    if not note_ids:
        return
    
    try:
        logger.debug("Checking 1ノート=1カード constraint", extra={
            "extra_fields": {
                "total_notes": len(note_ids),
                "sample_size": min(10, len(note_ids)),
            }
        })
        notes = notes_info(note_ids[:10])  # sample
        for note in notes:
            card_ids = note.get("cards", [])
            if len(card_ids) != 1:
                logger.error("1ノート=1カード constraint violated", extra={
                    "extra_fields": {
                        "note_id": note.get("noteId"),
                        "card_count": len(card_ids),
                    }
                })
                raise AnkiError(
                    f"note {note.get('noteId')} has {len(card_ids)} cards (expected 1)",
                    code="ONE_CARD_PER_NOTE_VIOLATION",
                    user_message=f"ノート {note.get('noteId')} にカードが {len(card_ids)} 個あります（期待値: 1）",
                    details={"note_id": note.get("noteId"), "card_count": len(card_ids)},
                )
        logger.debug("1ノート=1カード check passed", extra={
            "extra_fields": {"checked_notes": len(notes)}
        })
    except AnkiError:
        raise
    except Exception as exc:
        log_exception(
            logger,
            "1ノート=1カード check failed",
            exc,
            note_count=len(note_ids),
        )
        raise AnkiError(
            "1ノート=1カード検証失敗",
            code="ONE_CARD_PER_NOTE_CHECK_FAILED",
            user_message="1ノート=1カードの検証に失敗しました",
        ) from exc
