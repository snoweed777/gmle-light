"""Config merger."""

from __future__ import annotations

from typing import Any, Dict

from . import constants


def defaults() -> Dict[str, Any]:
    """Get default config from constants."""
    return {
        "params": {
            "total": constants.TOTAL_DEFAULT,
            "new_total": constants.NEW_TOTAL_DEFAULT,
            "maintain_total": constants.MAINTAIN_TOTAL_DEFAULT,
            "coverage": constants.COVERAGE_DEFAULT,
            "improve": constants.IMPROVE_DEFAULT,
            "reward_cap": constants.REWARD_CAP_DEFAULT,
            "domain_cap_steps": list(constants.DOMAIN_CAP_STEPS_DEFAULT),
            "excerpt_min": constants.EXCERPT_MIN,
            "excerpt_max": constants.EXCERPT_MAX,
            "rationale_quote_max": constants.RATIONALE_QUOTE_MAX,
        }
    }


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def merge_configs(
    global_cfg: Dict[str, Any],
    local_cfg: Dict[str, Any],
    space_cfg: Dict[str, Any],
    env_cfg: Dict[str, Any],
    cli_cfg: Dict[str, Any],
) -> Dict[str, Any]:
    """Merge configs with priority: CLI > env > space yaml > local yaml > global yaml > constants."""
    # Start with defaults
    merged = defaults()
    
    # Apply global config (deep merge)
    if global_cfg:
        merged = _deep_merge(merged, global_cfg)
    
    # Apply local config (deep merge)
    if local_cfg:
        merged = _deep_merge(merged, local_cfg)
    
    # Apply space config (deep merge, but space-specific keys take precedence)
    if space_cfg:
        # Handle params separately
        if "params" in space_cfg:
            if "params" not in merged:
                merged["params"] = {}
            merged["params"].update(space_cfg["params"] or {})
        
        # Handle space-specific keys
        for k in ("deck_bank", "data_root", "sources_root", "space_id"):
            if k in space_cfg:
                merged[k] = space_cfg[k]

        # Deep merge other keys
        for k, v in space_cfg.items():
            if k not in ("params", "deck_bank", "data_root", "sources_root", "space_id"):
                if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
                    merged[k] = _deep_merge(merged[k], v)
                else:
                    merged[k] = v
    
    # Apply env overrides (flat structure)
    for k, v in env_cfg.items():
        if k in merged.get("params", {}) and isinstance(v, (int, list)):
            merged["params"][k] = v
        elif k == "domain_cap_steps" and isinstance(v, str):
            # Parse comma-separated list
            from .env_loader import _parse_int_list
            merged["params"][k] = _parse_int_list(v)
        else:
            merged[k] = v

    # Apply CLI overrides (highest priority)
    for k, v in cli_cfg.items():
        if k in merged.get("params", {}):
            merged["params"][k] = v
        elif k in {"deck_bank", "data_root", "sources_root", "space_id"}:
            merged[k] = v
        else:
            merged[k] = v

    return merged
