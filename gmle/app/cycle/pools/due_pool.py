"""DuePool: due昇順（同点処理あり）."""

from __future__ import annotations

from typing import Any, Dict, List


def select_due_pool(
    base_notes: List[Dict[str, Any]],
    base_cards: List[Dict[str, Any]],
    exclude_note_ids: set[int],
) -> List[int]:
    """Select DuePool: due昇順 (due asc, lapses desc, note_id asc)."""
    note_id_to_card = {c["note"]: c for c in base_cards}
    candidates = []
    for note in base_notes:
        note_id = note["noteId"]
        if note_id in exclude_note_ids:
            continue
        card = note_id_to_card.get(note_id)
        if not card:
            continue
        candidates.append((card.get("due", 0), card.get("lapses", 0), note_id))
    candidates.sort(key=lambda x: (x[0], -x[1], x[2]))
    return [note_id for _, _, note_id in candidates]
