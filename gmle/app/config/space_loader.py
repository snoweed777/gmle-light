"""Space YAML loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from gmle.app.infra.errors import ConfigError


def load_space_yaml(root: Path, space_id: str) -> Dict[str, Any]:
    """Load space YAML config."""
    path = root / "config" / "spaces" / f"{space_id}.yaml"
    if not path.exists():
        raise ConfigError(f"space config not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"space config invalid format: {path}")
    return data
