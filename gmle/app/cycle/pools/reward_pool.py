"""RewardPool: 前日cycle集合のうち「良好」最大REWARD_CAP."""

from __future__ import annotations

from typing import Any, Dict, List


def select_reward_pool(
    base_notes: List[Dict[str, Any]],
    yesterday_tag: str,
    reward_cap: int,
) -> List[int]:
    """Select RewardPool from yesterday cycle notes."""
    yesterday_notes = [n for n in base_notes if yesterday_tag in n.get("tags", [])]
    if not yesterday_notes:
        return []
    yesterday_notes.sort(key=lambda n: (n.get("noteId", 0)))
    return [n["noteId"] for n in yesterday_notes[:reward_cap]]
