"""AnkiConnect client."""

from __future__ import annotations

from typing import Any, Dict, List

from gmle.app.config.getter import get_api_config, get_anki_config
from gmle.app.http.base import request
from gmle.app.infra.errors import AnkiError


def invoke(action: str, params: Dict[str, Any] | None = None, config: Dict[str, Any] | None = None) -> Any:
    """Invoke AnkiConnect action."""
    api_config = get_api_config(config)
    anki_config = api_config["anki"]
    connect_url = anki_config["connect_url"]
    connect_version = anki_config["connect_version"]
    
    payload = {"action": action, "version": connect_version, "params": params or {}}
    try:
        resp = request("POST", connect_url, json=payload)
        # AnkiConnect may return JSON as string
        if isinstance(resp, str):
            import json
            resp = json.loads(resp)
        if not isinstance(resp, dict):
            raise AnkiError(f"invalid response format: {type(resp)}")
        if "error" in resp and resp["error"] is not None:
            raise AnkiError(f"anki error: {resp['error']}")
        return resp.get("result")
    except Exception as exc:
        if isinstance(exc, AnkiError):
            raise
        raise AnkiError(f"anki invoke failed: {action}") from exc


def find_notes(query: str) -> List[int]:
    """Find note IDs by query."""
    result = invoke("findNotes", {"query": query})
    if not isinstance(result, list):
        raise AnkiError(f"findNotes returned non-list: {type(result)}")
    return [int(nid) for nid in result]


def notes_info(note_ids: List[int]) -> List[Dict[str, Any]]:
    """Get note info."""
    result = invoke("notesInfo", {"notes": note_ids})
    if not isinstance(result, list):
        raise AnkiError(f"notesInfo returned non-list: {type(result)}")
    return result


def cards_info(card_ids: List[int]) -> List[Dict[str, Any]]:
    """Get card info."""
    result = invoke("cardsInfo", {"cards": card_ids})
    if not isinstance(result, list):
        raise AnkiError(f"cardsInfo returned non-list: {type(result)}")
    return result


def model_names() -> List[str]:
    """Get model names."""
    result = invoke("modelNames")
    if not isinstance(result, list):
        raise AnkiError(f"modelNames returned non-list: {type(result)}")
    return result


def model_field_names(model_name: str) -> List[str]:
    """Get field names for a model."""
    result = invoke("modelFieldNames", {"modelName": model_name})
    if not isinstance(result, list):
        raise AnkiError(f"modelFieldNames returned non-list: {type(result)}")
    return result


def build_base_query(deck_bank: str, config: Dict[str, Any] | None = None) -> str:
    """Build BASE query (spec 9.1)."""
    anki_config = get_anki_config(config)
    note_type_name = anki_config["note_type_name"]
    return f'deck:"{deck_bank}" note:"{note_type_name}" tag:status::generated -tag:status::retired'


def deck_names() -> List[str]:
    """Get deck names."""
    result = invoke("deckNames")
    if not isinstance(result, list):
        raise AnkiError(f"deckNames returned non-list: {type(result)}")
    return result


def create_deck(deck_name: str) -> int:
    """Create deck if not exists."""
    result = invoke("createDeck", {"deck": deck_name})
    if not isinstance(result, int):
        raise AnkiError(f"createDeck returned non-int: {type(result)}")
    return result


def create_model(model_name: str, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Create note type if not exists."""
    in_order_fields = [
        "ID", "Question", "ChoiceA", "ChoiceB", "ChoiceC", "ChoiceD",
        "Answer", "RationaleQuote", "RationaleExplain",
        "SourceTitle", "SourceLocator", "SourceURL",
        "DomainPath", "MetaJSON"
    ]
    card_templates = [
        {
            "Name": "Card 1",
            "Front": "{{Question}}\n\n{{ChoiceA}}\n{{ChoiceB}}\n{{ChoiceC}}\n{{ChoiceD}}",
            "Back": "{{FrontSide}}\n\n<hr id=answer>\n\nAnswer: {{Answer}}\n\nRationale:\n{{RationaleQuote}}\n{{RationaleExplain}}\n\nSource: {{SourceTitle}} - {{SourceLocator}}\n{{#SourceURL}}\nURL: {{SourceURL}}\n{{/SourceURL}}"
        }
    ]
    params = {
        "modelName": model_name,
        "inOrderFields": in_order_fields,
        "css": "",
        "cardTemplates": card_templates
    }
    result = invoke("createModel", params)
    if not isinstance(result, dict):
        raise AnkiError(f"createModel returned non-dict: {type(result)}")
    return result


def sync(config: Dict[str, Any] | None = None) -> None:
    """Sync Anki with AnkiWeb (automatic sync)."""
    api_config = get_api_config(config)
    anki_config = api_config["anki"]
    if not anki_config.get("auto_sync", True):
        return  # Auto-sync disabled
    invoke("sync", config=config)
