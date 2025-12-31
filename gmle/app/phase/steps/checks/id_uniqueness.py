"""ID uniqueness check (I7)."""

from __future__ import annotations

from typing import Dict, List

from gmle.app.adapters.anki_client import notes_info
from gmle.app.infra.errors import AnkiError
from gmle.app.infra.logger import get_logger, log_exception


def check_id_uniqueness(note_ids: List[int]) -> None:
    """Check ID uniqueness (I7)."""
    logger = get_logger()
    
    if not note_ids:
        return
    
    try:
        logger.debug("Checking ID uniqueness", extra={
            "extra_fields": {
                "note_count": len(note_ids),
            }
        })
        
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
            logger.error("Duplicate ID tags found", extra={
                "extra_fields": {
                    "duplicates": duplicates,
                }
            })
            raise AnkiError(
                f"duplicate ID tags: {duplicates}",
                code="DUPLICATE_ID_TAGS",
                user_message=f"重複したIDタグが見つかりました: {len(duplicates)}件",
                details={"duplicates": duplicates},
            )
        
        logger.debug("ID uniqueness check passed", extra={
            "extra_fields": {
                "unique_ids": len(id_tags),
            }
        })
    except AnkiError:
        raise
    except Exception as exc:
        log_exception(
            logger,
            "ID uniqueness check failed",
            exc,
            note_count=len(note_ids),
        )
        raise AnkiError(
            "ID一意検証失敗",
            code="ID_UNIQUENESS_CHECK_FAILED",
            user_message="ID一意性の検証に失敗しました",
        ) from exc
