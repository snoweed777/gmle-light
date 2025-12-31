"""Domain cap enforcement (spec 13.4)."""

from __future__ import annotations

from typing import Any, Dict, List


def apply_domain_cap(
    candidates: List[int],
    base_notes: List[Dict[str, Any]],
    cap_steps: tuple[int, ...],
    target_total: int,
) -> List[int]:
    """Apply domain cap with step relaxation."""
    note_id_to_note = {n["noteId"]: n for n in base_notes}
    result: List[int] = []
    for cap in cap_steps:
        domain_counts: Dict[str, int] = {}
        for note_id in candidates:
            if note_id in result:
                continue
            note = note_id_to_note.get(note_id)
            if not note:
                continue
            domain_path = _extract_domain_path(note)
            current_count = domain_counts.get(domain_path, 0)
            if current_count >= cap:
                continue
            result.append(note_id)
            domain_counts[domain_path] = current_count + 1
            if len(result) >= target_total:
                break
        if len(result) >= target_total:
            break
    return result


def _extract_domain_path(note: Dict[str, Any]) -> str:
    """Extract domain_path from note."""
    fields = note.get("fields", {})
    domain_path_value = fields.get("DomainPath", {}).get("value", "unknown/unknown/unknown")
    if isinstance(domain_path_value, str):
        return domain_path_value
    return "unknown/unknown/unknown"
