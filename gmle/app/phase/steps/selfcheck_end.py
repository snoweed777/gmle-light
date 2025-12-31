"""Phase 9: Selfcheck End."""

from __future__ import annotations

from typing import Any, Dict

from gmle.app.adapters.anki_client import build_base_query, find_notes, notes_info
from gmle.app.cycle.cycle_apply import cleanup_cycle_tags


def execute(context: Dict[str, Any]) -> None:
    """Selfcheck End (Phase 9)."""
    deck_bank = context["deck_bank"]
    today_note_ids = context.get("today_note_ids", [])
    today_tag = f"cycle::{context.get('today_str', '')}"

    base_note_ids: list[int] = []
    try:
        query = build_base_query(deck_bank, config=context)
        base_note_ids = find_notes(query)
        notes = notes_info(base_note_ids)
        today_found = sum(1 for n in notes if today_tag in n.get("tags", []))
        # I1: Today集合はちょうど30ノート（BASE集合が30件以上の場合）
        # BASE集合が30件未満の場合は、BASE集合の件数と一致することを確認
        expected_count = min(30, len(base_note_ids))
        if len(today_note_ids) != expected_count or today_found != expected_count:
            cleanup_cycle_tags(base_note_ids)
            raise ValueError(f"Today count mismatch: expected {expected_count}, got {len(today_note_ids)}, found {today_found}")
    except Exception:
        if base_note_ids:
            cleanup_cycle_tags(base_note_ids)
        raise
