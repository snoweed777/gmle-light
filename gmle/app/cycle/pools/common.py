"""Common utilities for pool selection."""

from __future__ import annotations

from typing import Any, Dict, List


def build_note_id_to_card_map(base_cards: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """Build a mapping from note ID to card for efficient lookup.
    
    Args:
        base_cards: List of card dictionaries
        
    Returns:
        Dict mapping note_id -> card dict
    """
    return {c["note"]: c for c in base_cards}

