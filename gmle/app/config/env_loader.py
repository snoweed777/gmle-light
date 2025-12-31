"""Environment variable loader."""

from __future__ import annotations

import os
from typing import Any, Dict, List


def load_env_overrides() -> Dict[str, Any]:
    """Load environment variable overrides."""
    env_map = {
        "total": os.getenv("GMLE_TOTAL"),
        "new_total": os.getenv("GMLE_NEW_TOTAL"),
        "maintain_total": os.getenv("GMLE_MAINTAIN_TOTAL"),
        "coverage": os.getenv("GMLE_COVERAGE"),
        "improve": os.getenv("GMLE_IMPROVE"),
        "reward_cap": os.getenv("GMLE_REWARD_CAP"),
        "domain_cap_steps": os.getenv("GMLE_DOMAIN_CAP_STEPS"),
        "deck_bank": os.getenv("GMLE_DECK_BANK"),
        "data_root": os.getenv("GMLE_DATA_ROOT"),
        "sources_root": os.getenv("GMLE_SOURCES_ROOT"),
    }
    result: Dict[str, Any] = {}
    for key, val in env_map.items():
        if val is None:
            continue
        if key == "domain_cap_steps":
            result[key] = _parse_int_list(val)
        elif key in {"total", "new_total", "maintain_total", "coverage", "improve", "reward_cap"}:
            result[key] = int(val)
        else:
            result[key] = val
    return result


def _parse_int_list(value: str) -> List[int]:
    """Parse comma-separated int list."""
    return [int(x.strip()) for x in value.split(",") if x.strip()]
