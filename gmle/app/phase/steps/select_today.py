"""Phase 6: Select Today."""

from __future__ import annotations

from typing import Any, Dict

from gmle.app.cycle.today_select import select_today


def execute(context: Dict[str, Any]) -> None:
    """Select Today 30 (Phase 6)."""
    today_note_ids = select_today({
        "base_notes": context["base_notes"],
        "base_cards": context["base_cards"],
        "items": context["items"],
        "params": context["params"],
    })
    context["today_note_ids"] = today_note_ids
