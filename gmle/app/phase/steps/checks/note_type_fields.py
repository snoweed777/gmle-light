"""Note type and fields check."""

from __future__ import annotations

from gmle.app.adapters.anki_client import model_names, model_field_names
from gmle.app.infra.errors import AnkiError
from gmle.app.infra.logger import get_logger


REQUIRED_FIELDS = [
    "ID", "Question", "ChoiceA", "ChoiceB", "ChoiceC", "ChoiceD", "Answer",
    "RationaleQuote", "RationaleExplain", "SourceTitle", "SourceLocator", "SourceURL",
    "DomainPath", "MetaJSON",
]
NOTE_TYPE = "GMLE_MCQA"


def check_note_type_fields() -> None:
    """Check note type and fields integrity."""
    logger = get_logger()
    
    try:
        logger.debug("Checking note type and fields", extra={
            "extra_fields": {
                "note_type": NOTE_TYPE,
                "required_fields_count": len(REQUIRED_FIELDS),
            }
        })
        model_list = model_names()
        if NOTE_TYPE not in model_list:
            logger.error("Note type not found", extra={
                "extra_fields": {
                    "note_type": NOTE_TYPE,
                    "available_models": model_list,
                }
            })
            raise AnkiError(
                f"note type not found: {NOTE_TYPE}",
                code="NOTE_TYPE_NOT_FOUND",
                user_message=f"ノートタイプが見つかりません: {NOTE_TYPE}",
                details={"available_models": model_list},
            )
        field_names = model_field_names(NOTE_TYPE)
        missing_fields = set(REQUIRED_FIELDS) - set(field_names)
        if missing_fields:
            logger.error("Missing required fields", extra={
                "extra_fields": {
                    "missing_fields": list(missing_fields),
                    "available_fields": field_names,
                }
            })
            raise AnkiError(
                f"missing fields: {missing_fields}",
                code="MISSING_FIELDS",
                user_message=f"必須フィールドが不足しています: {missing_fields}",
                details={"missing_fields": list(missing_fields), "available_fields": field_names},
            )
        logger.debug("Note type and fields check passed", extra={
            "extra_fields": {
                "note_type": NOTE_TYPE,
                "field_count": len(field_names),
            }
        })
    except AnkiError:
        raise
    except Exception as exc:
        logger.error("Note type and fields check failed", exc_info=True, extra={
            "extra_fields": {
                "note_type": NOTE_TYPE,
            }
        })
        raise AnkiError(
            "note type and fields check failed",
            code="NOTE_TYPE_FIELDS_CHECK_FAILED",
            user_message="ノートタイプとフィールドの検証に失敗しました",
        ) from exc
