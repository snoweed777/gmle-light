"""Gates (spec 15.3)."""

from __future__ import annotations

from typing import Any, Dict


def hard_gate(item: Dict[str, Any], excerpt: str) -> tuple[bool, str]:
    """Hard Gate: reject if fails (spec 15.3)."""
    if item["answer"] not in ("A", "B", "C", "D"):
        return False, "invalid answer"
    if len(item["choices"]) != 4:
        return False, "invalid choices count"
    rationale_quote = item["rationale"]["quote"]
    if len(rationale_quote) > 100:
        return False, "rationale quote too long"
    if rationale_quote not in excerpt:
        return False, "rationale quote not in excerpt"
    return True, ""


def soft_gate(item: Dict[str, Any]) -> bool:
    """Soft Gate: mark with qc::soft_fail if fails."""
    if item.get("format") not in ("F", "W", "A"):
        return False
    if item.get("depth") not in (1, 2, 3):
        return False
    return True
