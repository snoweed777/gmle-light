"""Config-related endpoints."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException

from gmle.app.api.rest.errors import raise_not_found
from gmle.app.api.rest.models import ConfigResponse, ConfigUpdateRequest
from gmle.app.config.loader import load_config

router = APIRouter(prefix="/spaces/{space_id}/config", tags=["config"])


@router.get("", response_model=ConfigResponse)
async def get_config(space_id: str) -> ConfigResponse:
    """Get space configuration."""
    try:
        config = load_config({"space": space_id})
        paths = {k: str(v) for k, v in config["paths"].items()}
        return ConfigResponse(
            space_id=space_id,
            params=config["params"],
            paths=paths,
        )
    except Exception:
        raise_not_found("Space", space_id)
        return ConfigResponse(space_id="", params={}, paths={})  # Never reached


@router.put("", response_model=ConfigResponse)
async def update_config(
    space_id: str,
    request: ConfigUpdateRequest,
) -> ConfigResponse:
    """Update space configuration."""
    config_file = Path(f"config/spaces/{space_id}.yaml")
    
    if not config_file.exists():
        raise_not_found("Space", space_id)
    
    try:
        # Load current YAML file
        with open(config_file, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)
        
        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = config_file.with_suffix(f".{timestamp}.backup")
        shutil.copy2(config_file, backup_file)
        
        # Update params if provided
        if request.params:
            yaml_data["params"] = request.params
        
        # Write updated YAML
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)
        
        # Reload config to return updated values
        config = load_config({"space": space_id})
        paths = {k: str(v) for k, v in config["paths"].items()}
        
        return ConfigResponse(
            space_id=space_id,
            params=config["params"],
            paths=paths,
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update config: {str(e)}"
        )

