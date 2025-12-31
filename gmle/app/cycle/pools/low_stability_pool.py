"""LowStabilityPool: ivl短い or reps少ない."""

from __future__ import annotations

from typing import Any, Dict, List

from .common import build_note_id_to_card_map


def select_low_stability_pool(
    base_notes: List[Dict[str, Any]],
    base_cards: List[Dict[str, Any]],
    exclude_note_ids: set[int],
) -> List[int]:
    """Select LowStabilityPool: ivl短い or reps少ない (ivl asc, reps asc, due asc, note_id asc)."""
    note_id_to_card = build_note_id_to_card_map(base_cards)
    candidates = []
    for note in base_notes:
        note_id = note["noteId"]
        if note_id in exclude_note_ids:
            continue
        card = note_id_to_card.get(note_id)
        if not card:
            continue
        candidates.append((card.get("ivl", 0), card.get("reps", 0), card.get("due", 0), note_id))
    candidates.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
    return [note_id for _, _, _, note_id in candidates]
