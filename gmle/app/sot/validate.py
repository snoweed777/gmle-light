"""Validation helpers for SOT."""

from __future__ import annotations

from typing import Any, Dict, List

from gmle.app.infra.errors import SOTError


def validate_items(items: List[Dict[str, Any]]) -> None:
    """Validate items structure and constraints (spec 5.2)."""
    if not isinstance(items, list):
        raise SOTError("items must be a list")
    for idx, item in enumerate(items):
        _validate_item(item, idx)


def _validate_item(item: Dict[str, Any], idx: int) -> None:
    """Validate single item."""
    required_fields = ["id", "source_id", "domain_path", "format", "depth", "question", "choices", "answer", "rationale", "source", "meta", "retired"]
    for field in required_fields:
        if field not in item:
            raise SOTError(f"item[{idx}] missing required field: {field}")

    if not isinstance(item["id"], str) or not item["id"].startswith("gmle::"):
        raise SOTError(f"item[{idx}] invalid id format: {item['id']}")

    if item["format"] not in ("F", "W", "A"):
        raise SOTError(f"item[{idx}] invalid format: {item['format']}")

    if item["depth"] not in (1, 2, 3):
        raise SOTError(f"item[{idx}] invalid depth: {item['depth']}")

    if not isinstance(item["choices"], list) or len(item["choices"]) != 4:
        raise SOTError(f"item[{idx}] choices must be list of 4")

    if item["answer"] not in ("A", "B", "C", "D"):
        raise SOTError(f"item[{idx}] invalid answer: {item['answer']}")

    rationale = item["rationale"]
    if not isinstance(rationale, dict) or "quote" not in rationale or "explain" not in rationale:
        raise SOTError(f"item[{idx}] invalid rationale structure")
    if len(rationale["quote"]) > 100:
        raise SOTError(f"item[{idx}] rationale.quote exceeds 100 chars")

    if not isinstance(item["retired"], bool):
        raise SOTError(f"item[{idx}] retired must be bool")
