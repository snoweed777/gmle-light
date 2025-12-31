"""Paths and deck resolution check (Sx1-Sx4)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from gmle.app.infra.errors import ConfigError


def check_paths_deck(paths: Dict[str, Any], space_id: str, deck_bank: str) -> None:
    """Check paths and deck resolution (Sx1-Sx4)."""
    if not deck_bank.startswith("GMLE::Bank::"):
        raise ConfigError(f"invalid deck_bank format: {deck_bank}")
    expected_deck_suffix = f"GMLE::Bank::{space_id}"
    if deck_bank != expected_deck_suffix:
        raise ConfigError(f"deck_bank mismatch: {deck_bank} != {expected_deck_suffix}")

    for key in ("data_root", "sources_root"):
        path = paths.get(key)
        if not isinstance(path, Path):
            raise ConfigError(f"path resolution failed: {key}")
