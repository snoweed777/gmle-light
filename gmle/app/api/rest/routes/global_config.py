"""Global configuration endpoints."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import yaml
from fastapi import APIRouter, HTTPException

from gmle.app.api.rest.models import GlobalConfigResponse, GlobalConfigUpdateRequest
from gmle.app.config.env_paths import get_config_dir

router = APIRouter(prefix="/config/global", tags=["global_config"])


def _load_global_config() -> Dict[str, Any]:
    """Load global config from gmle.yaml."""
    config_file = get_config_dir() / "gmle.yaml"
    
    if not config_file.exists():
        raise HTTPException(status_code=404, detail="Global config not found")

    with open(config_file, encoding="utf-8") as f:
        result: Dict[str, Any] = yaml.safe_load(f) or {}
        return result


def _save_global_config(config: Dict[str, Any]) -> None:
    """Save global config to gmle.yaml with backup."""
    config_file = get_config_dir() / "gmle.yaml"

    # Create backup
    if config_file.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = config_file.with_suffix(f".{timestamp}.backup")
        shutil.copy2(config_file, backup_file)

    # Save updated config
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


@router.get("", response_model=GlobalConfigResponse)
async def get_global_config() -> GlobalConfigResponse:
    """Get global configuration."""
    try:
        config = _load_global_config()
        
        return GlobalConfigResponse(
            params=config.get("params", {}),
            api=config.get("api", {}),
            logging=config.get("logging", {}),
            http=config.get("http", {}),
            rate_limit=config.get("rate_limit", {}),
            message=None,
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_global_config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load global config: {str(e)}")


@router.put("", response_model=GlobalConfigResponse)
async def update_global_config(
    request: GlobalConfigUpdateRequest,
) -> GlobalConfigResponse:
    """Update global configuration."""
    config = _load_global_config()

    # Update params
    if request.params:
        config.setdefault("params", {}).update(request.params)

    # Update API settings
    if request.api:
        config.setdefault("api", {}).update(request.api)

    # Update logging settings
    if request.logging:
        config.setdefault("logging", {}).update(request.logging)

    # Update HTTP settings
    if request.http:
        config.setdefault("http", {}).update(request.http)

    # Update rate limit settings
    if request.rate_limit:
        config.setdefault("rate_limit", {}).update(request.rate_limit)

    # Save updated config
    _save_global_config(config)

    return await get_global_config()
