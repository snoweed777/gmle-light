"""Add note to Anki."""

from __future__ import annotations

from typing import Any, Dict, List

from gmle.app.adapters.anki_client import invoke
from gmle.app.infra.errors import AnkiError


def add_note(item: Dict[str, Any], deck_bank: str, note_type: str) -> int:
    """Add note to Anki (spec 16.2)."""
    fields = _build_fields(item)
    tags = _build_tags(item)
    note = {
        "deckName": deck_bank,
        "modelName": note_type,
        "fields": fields,
        "tags": tags,
    }
    try:
        result = invoke("addNote", {"note": note})
        if not isinstance(result, int):
            raise AnkiError(f"addNote returned non-int: {type(result)}")
        return result
    except Exception as exc:
        raise AnkiError(f"addNote failed: {item.get('id', 'unknown')}") from exc


def _build_fields(item: Dict[str, Any]) -> Dict[str, str]:
    """Build Anki fields from item."""
    import json
    source_url = item["source"].get("url") or ""
    meta_json = json.dumps(item["meta"], ensure_ascii=False) if item.get("meta") else "{}"
    
    # Handle rationale field variations (text, explain, or empty)
    rationale = item.get("rationale", {})
    rationale_explain = rationale.get("text") or rationale.get("explain", "")
    
    return {
        "ID": item["id"],
        "Question": item["question"],
        "ChoiceA": item["choices"][0],
        "ChoiceB": item["choices"][1],
        "ChoiceC": item["choices"][2],
        "ChoiceD": item["choices"][3],
        "Answer": item["answer"],
        "RationaleQuote": item["rationale"]["quote"],
        "RationaleExplain": rationale_explain,
        "SourceTitle": item["source"]["title"],
        "SourceLocator": item["source"]["locator"],
        "SourceURL": source_url,
        "DomainPath": item["domain_path"],
        "MetaJSON": meta_json,
    }


def _build_tags(item: Dict[str, Any]) -> List[str]:
    """Build Anki tags from item."""
    tags = [
        f'id::{item["id"]}',
        f'domain::{item["domain_path"].replace("/", "::")}',
        f'type::{item["format"]}',
        f'depth::{item["depth"]}',
        "status::generated",
    ]
    if item.get("retired", False):
        tags.append("status::retired")
    return tags
