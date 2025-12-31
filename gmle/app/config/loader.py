"""Config loader with priority: CLI > env > space yaml > local yaml > global yaml > constants."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from gmle.app.infra.errors import ConfigError
from .env_loader import load_env_overrides
from .global_loader import load_global_yaml, load_local_yaml
from .merger import merge_configs
from .paths import resolve_paths
from .space_loader import load_space_yaml


def load_config(cli_args: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Load merged config with priority: CLI > env > space yaml > local yaml > global yaml > constants."""
    from .getter import set_config
    
    cli = cli_args or {}
    root = Path(cli.get("root") or Path.cwd())
    space_id = cli.get("space") or os.getenv("GMLE_SPACE")
    if not space_id:
        raise ConfigError("space_id is required (CLI --space or GMLE_SPACE)")

    global_cfg = load_global_yaml(root)
    local_cfg = load_local_yaml(root)
    space_cfg = load_space_yaml(root, space_id)
    env_cfg = load_env_overrides()
    merged = merge_configs(global_cfg, local_cfg, space_cfg, env_cfg, cli)
    merged["space_id"] = space_id
    merged["paths"] = resolve_paths(root, space_id, merged)
    
    # Cache config for getter utilities
    set_config(merged)
    
    return merged
