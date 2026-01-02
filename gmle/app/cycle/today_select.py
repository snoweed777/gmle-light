"""Deterministic Today selection (spec 13)."""

from __future__ import annotations

from typing import Any, Dict, List, Set

from .domain_cap import apply_domain_cap
from .pools.due_pool import select_due_pool
from .pools.failed_pool import select_failed_pool
from .pools.fallback_pool import select_fallback_pool
from .pools.low_stability_pool import select_low_stability_pool
from .pools.reward_pool import select_reward_pool


def select_today(inputs: Dict[str, Any]) -> List[int]:
    """Return Today note IDs deterministically (spec 13)."""
    base_notes = inputs["base_notes"]
    base_cards = inputs["base_cards"]
    items = inputs["items"]
    params = inputs["params"]
    yesterday_tag = f"cycle::{_yesterday_str()}"

    retired_item_ids = _get_retired_item_ids(items)
    active_notes = [n for n in base_notes if not _is_retired(n, retired_item_ids)]
    active_cards = [c for c in base_cards if c["note"] in {n["noteId"] for n in active_notes}]

    # Get reward_cap with fallback to default value
    reward_cap = params.get("reward_cap", 3)
    reward = select_reward_pool(active_notes, yesterday_tag, reward_cap)
    exclude = set(reward)

    # Get params with fallback defaults
    maintain_total = params.get("maintain_total", 20)
    new_total = params.get("new_total", 10)
    total = params.get("total", 30)
    domain_cap_steps = tuple(params.get("domain_cap_steps", [6, 7, 8, 9999]))

    due = select_due_pool(active_notes, active_cards, exclude)
    exclude.update(due[:maintain_total])

    failed = select_failed_pool(active_notes, active_cards, exclude)
    exclude.update(failed)

    low_stability = select_low_stability_pool(active_notes, active_cards, exclude)
    exclude.update(low_stability)

    fallback = select_fallback_pool(active_notes, exclude)

    maintain_candidates = due[:maintain_total] + failed + low_stability
    maintain = apply_domain_cap(maintain_candidates, active_notes, domain_cap_steps, maintain_total)

    # For new, use remaining maintain_candidates + fallback
    new_candidates = maintain_candidates[len(maintain):] + fallback
    new = apply_domain_cap(new_candidates, active_notes, domain_cap_steps, new_total)

    # Ensure total reaches params["total"] by adding fallback if needed
    current_total = len(set(reward + maintain + new))
    if current_total < total:
        remaining_needed = total - current_total
        current_set = set(reward + maintain + new)
        # Use all active notes that are not already selected
        all_active_note_ids = {n["noteId"] for n in active_notes}
        additional = [nid for nid in sorted(all_active_note_ids) if nid not in current_set][:remaining_needed]
        new.extend(additional)

    today = list(set(reward + maintain + new))[:total]
    return sorted(today)


def _get_retired_item_ids(items: List[Dict[str, Any]]) -> Set[str]:
    """Get retired item IDs from items.json."""
    return {item["id"] for item in items if item.get("retired", False)}


def _is_retired(note: Dict[str, Any], retired_item_ids: Set[str]) -> bool:
    """Check if note is retired by matching id tag with items.json."""
    tags = note.get("tags", [])
    for tag in tags:
        if tag.startswith("id::"):
            item_id = tag[4:]
            return item_id in retired_item_ids
    return False


def _yesterday_str() -> str:
    """Get yesterday date string."""
    from datetime import date, timedelta
    return (date.today() - timedelta(days=1)).isoformat()
