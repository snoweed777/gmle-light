"""Phase 3: Plan."""

from __future__ import annotations

from typing import Any, Dict

from gmle.app.cycle.cycle_plan import plan_today


def execute(context: Dict[str, Any]) -> None:
    """Plan today composition (Phase 3)."""
    plan_inputs = plan_today({
        "base_notes": context["base_notes"],
        "base_cards": context["base_cards"],
        "items": context["items"],
        "params": context["params"],
    })
    context["plan"] = plan_inputs
