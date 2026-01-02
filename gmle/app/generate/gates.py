"""Gates (spec 15.3)."""

from __future__ import annotations

from typing import Any, Dict


def hard_gate(item: Dict[str, Any], excerpt: str) -> tuple[bool, str]:
    """Hard Gate: reject if fails (spec 15.3)."""
    from gmle.app.infra.logger import get_logger, with_fields
    logger = get_logger()
    
    # Safe field access with validation
    answer = item.get("answer")
    if not answer or answer not in ("A", "B", "C", "D"):
        logger.debug("Hard gate: invalid answer", **with_fields(logger,
            answer=answer,
            available_fields=list(item.keys()),
        ))
        return False, f"invalid or missing answer: {answer}"
    
    choices = item.get("choices", [])
    if len(choices) != 4:
        logger.debug("Hard gate: invalid choices count", **with_fields(logger,
            choices_count=len(choices),
            choices=choices,
        ))
        return False, f"invalid choices count: {len(choices)}"
    
    question = item.get("question", "")
    if not question:
        logger.debug("Hard gate: missing question", **with_fields(logger,
            available_fields=list(item.keys()),
        ))
        return False, "missing question"
    
    rationale = item.get("rationale", {})
    if not isinstance(rationale, dict):
        logger.debug("Hard gate: rationale not a dict", **with_fields(logger,
            rationale_type=type(rationale).__name__,
            rationale=str(rationale)[:100],
        ))
        return False, "rationale must be a dict"
    
    rationale_quote = rationale.get("quote", "")
    rationale_text = rationale.get("text") or rationale.get("explain", "")
    
    if not rationale_quote:
        logger.debug("Hard gate: missing rationale quote", **with_fields(logger,
            rationale_keys=list(rationale.keys()),
        ))
        return False, "missing rationale quote"
    
    if not rationale_text:
        logger.debug("Hard gate: missing rationale text/explain", **with_fields(logger,
            rationale_keys=list(rationale.keys()),
        ))
        return False, "missing rationale text or explain"
    
    if len(rationale_quote) > 100:
        logger.debug("Hard gate: rationale quote too long", **with_fields(logger,
            quote_length=len(rationale_quote),
            quote_preview=rationale_quote[:100],
        ))
        return False, f"rationale quote too long: {len(rationale_quote)} chars"
    
    if rationale_quote not in excerpt:
        logger.debug("Hard gate: rationale quote not in excerpt", **with_fields(logger,
            quote=rationale_quote,
            excerpt_length=len(excerpt),
            excerpt_preview=excerpt[:100],
        ))
        return False, "rationale quote not found in excerpt"
    
    return True, ""


def soft_gate(item: Dict[str, Any]) -> bool:
    """Soft Gate: mark with qc::soft_fail if fails."""
    if item.get("format") not in ("F", "W", "A"):
        return False
    if item.get("depth") not in (1, 2, 3):
        return False
    return True
