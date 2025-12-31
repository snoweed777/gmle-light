"""Global configuration endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from gmle.app.api.rest.models import GlobalConfigResponse, GlobalConfigUpdateRequest
from gmle.app.config.yaml_io import load_global_yaml_config, save_global_yaml_config
from gmle.app.infra.errors import ConfigError
from gmle.app.infra.logger import get_logger, log_exception

router = APIRouter(prefix="/config/global", tags=["global_config"])


@router.get("", response_model=GlobalConfigResponse)
async def get_global_config() -> GlobalConfigResponse:
    """Get global configuration."""
    logger = get_logger()
    
    try:
        config = load_global_yaml_config()
        
        return GlobalConfigResponse(
            params=config.get("params", {}),
            api=config.get("api", {}),
            logging=config.get("logging", {}),
            http=config.get("http", {}),
            rate_limit=config.get("rate_limit", {}),
            message=None,
        )
    except HTTPException:
        raise
    except ConfigError as exc:
        log_exception(logger, "Config error in get_global_config", exc)
        raise HTTPException(status_code=500, detail=f"Failed to load global config: {str(exc)}")
    except Exception as exc:
        log_exception(logger, "Unexpected error in get_global_config", exc)
        raise HTTPException(status_code=500, detail=f"Failed to load global config: {str(exc)}")


@router.put("", response_model=GlobalConfigResponse)
async def update_global_config(
    request: GlobalConfigUpdateRequest,
) -> GlobalConfigResponse:
    """Update global configuration."""
    config = load_global_yaml_config()

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
    save_global_yaml_config(config)

    return await get_global_config()
