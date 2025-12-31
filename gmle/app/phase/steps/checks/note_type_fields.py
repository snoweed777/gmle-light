"""Note type and fields check."""

from __future__ import annotations

from gmle.app.adapters.anki_client import model_names, model_field_names
from gmle.app.infra.errors import AnkiError


REQUIRED_FIELDS = [
    "ID", "Question", "ChoiceA", "ChoiceB", "ChoiceC", "ChoiceD", "Answer",
    "RationaleQuote", "RationaleExplain", "SourceTitle", "SourceLocator", "SourceURL",
    "DomainPath", "MetaJSON",
]
NOTE_TYPE = "GMLE_MCQA"


def check_note_type_fields() -> None:
    """Check note type and fields integrity."""
    model_list = model_names()
    if NOTE_TYPE not in model_list:
        raise AnkiError(f"note type not found: {NOTE_TYPE}")
    field_names = model_field_names(NOTE_TYPE)
    missing_fields = set(REQUIRED_FIELDS) - set(field_names)
    if missing_fields:
        raise AnkiError(f"missing fields: {missing_fields}")
