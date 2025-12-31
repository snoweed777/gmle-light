"""Phase 2: Load."""

from __future__ import annotations

from typing import Any, Dict

from gmle.app.adapters.anki_client import cards_info
from gmle.app.cycle.base_fetch import fetch_base_notes_info
from gmle.app.sot.items_io import read_items
from gmle.app.sot.ledger_io import read_ledger
from gmle.app.sot.queue_io import read_queue


def execute(context: Dict[str, Any]) -> None:
    """Load items/ledger/queue/Anki state (Phase 2)."""
    paths = context["paths"]
    deck_bank = context["deck_bank"]

    items = read_items(paths["items"])
    ledger = read_ledger(paths["ledger"])
    queue = read_queue(paths["queue"])
    base_notes = fetch_base_notes_info(deck_bank)
    base_note_ids = [n["noteId"] for n in base_notes]
    base_cards = []
    if base_note_ids:
        card_ids = []
        for note in base_notes:
            card_ids.extend(note.get("cards", []))
        if card_ids:
            base_cards = cards_info(card_ids)

    context["items"] = items
    context["ledger"] = ledger
    context["queue"] = queue
    context["base_notes"] = base_notes
    context["base_note_ids"] = base_note_ids
    context["base_cards"] = base_cards
