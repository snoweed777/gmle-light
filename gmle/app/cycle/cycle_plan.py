"""Cycle planning model."""

from __future__ import annotations

from typing import Any, Dict


def plan_today(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Build plan inputs for Today selection."""
    return {
        "base_notes": inputs["base_notes"],
        "base_cards": inputs["base_cards"],
        "items": inputs["items"],
        "params": inputs["params"],
    }
