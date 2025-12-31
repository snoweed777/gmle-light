"""Global config loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from gmle.app.infra.errors import ConfigError


def load_global_yaml(root: Path) -> Dict[str, Any]:
    """Load global YAML config (config/gmle.yaml)."""
    path = root / "config" / "gmle.yaml"
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            raise ConfigError(f"global config invalid format: {path}")
        return data
    except Exception as exc:
        raise ConfigError(f"failed to load global config: {path}") from exc


def load_local_yaml(root: Path) -> Dict[str, Any]:
    """Load local YAML config (config/gmle.local.yaml, optional)."""
    path = root / "config" / "gmle.local.yaml"
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            raise ConfigError(f"local config invalid format: {path}")
        return data
    except Exception as exc:
        raise ConfigError(f"failed to load local config: {path}") from exc

