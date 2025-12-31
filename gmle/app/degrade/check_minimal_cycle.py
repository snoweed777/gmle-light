"""Check minimal cycle conditions (spec 12.2)."""

from __future__ import annotations

from typing import Any, Dict, List

from gmle.app.adapters.anki_client import build_base_query, find_notes, notes_info


def check_minimal_cycle_conditions(deck_bank: str, config: Dict[str, Any] | None = None) -> tuple[bool, List[int], str]:
    """Check minimal cycle conditions (spec 12.2)."""
    try:
        query = build_base_query(deck_bank, config=config)
        base_note_ids = find_notes(query)
    except Exception as exc:
        return False, [], f"BASE fetch failed: {exc}"

    if not base_note_ids:
        return False, [], "BASE is empty"

    try:
        notes = notes_info(base_note_ids[:5])
        retired_count = sum(1 for n in notes if "status::retired" in n.get("tags", []))
        active_count = len(base_note_ids) - retired_count
    except Exception as exc:
        return False, [], f"retired check failed: {exc}"

    if active_count < 30:
        return False, [], f"active notes < 30: {active_count}"

    return True, base_note_ids, ""
