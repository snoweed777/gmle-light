"""LLM configuration endpoints."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException

from gmle.app.api.rest.models import (
    LLMConfigResponse,
    LLMConfigUpdateRequest,
    LLMProviderInfo,
)
from gmle.app.config.secrets import SecretsManager
from gmle.app.config.yaml_io import load_global_yaml_config, save_global_yaml_config
from gmle.app.infra.errors import ConfigError
from gmle.app.infra.logger import get_logger, log_exception

router = APIRouter(prefix="/config/llm", tags=["llm_config"])


@router.get("", response_model=LLMConfigResponse)
async def get_llm_config() -> LLMConfigResponse:
    """Get LLM configuration."""
    logger = get_logger()
    
    try:
        config = load_global_yaml_config()
        llm_config = config.get("llm", {})

        active_provider = llm_config.get("active_provider", "cohere")
        providers_config = llm_config.get("providers", {})

        secrets_manager = SecretsManager()
        providers = {}

        for provider_name, provider_cfg in providers_config.items():
            # Check if API key is configured
            api_key_env = f"{provider_name.upper()}_API_KEY"
            api_key_configured = bool(
                os.getenv(api_key_env) or secrets_manager.get_secret(api_key_env)
            )

            providers[provider_name] = LLMProviderInfo(
                api_url=provider_cfg.get("api_url", ""),
                default_model=provider_cfg.get("default_model", ""),
                available_models=provider_cfg.get("available_models", []),
                api_key_configured=api_key_configured,
            )

        return LLMConfigResponse(active_provider=active_provider, providers=providers)
    except HTTPException:
        raise
    except ConfigError as exc:
        log_exception(logger, "Config error in get_llm_config", exc)
        raise HTTPException(status_code=500, detail=f"Failed to load LLM config: {str(exc)}")
    except Exception as exc:
        log_exception(logger, "Unexpected error in get_llm_config", exc)
        raise HTTPException(status_code=500, detail=f"Failed to load LLM config: {str(exc)}")


@router.put("", response_model=LLMConfigResponse)
async def update_llm_config(
    request: LLMConfigUpdateRequest,
) -> LLMConfigResponse:
    """Update LLM configuration."""
    logger = get_logger()
    
    try:
        config = load_global_yaml_config()

        if "llm" not in config:
            config["llm"] = {}

        # Update active provider
        if request.active_provider:
            config["llm"]["active_provider"] = request.active_provider

        # Update provider configurations
        if request.provider_config:
            secrets_manager = SecretsManager()

            for provider_name, provider_data in request.provider_config.items():
                # Update API key if provided
                if "api_key" in provider_data:
                    api_key = provider_data["api_key"]
                    if api_key:
                        api_key_env = f"{provider_name.upper()}_API_KEY"
                        secrets_manager.set_secret(api_key_env, api_key)

                # Update default model if provided
                if "default_model" in provider_data:
                    if "providers" not in config["llm"]:
                        config["llm"]["providers"] = {}
                    if provider_name not in config["llm"]["providers"]:
                        config["llm"]["providers"][provider_name] = {}

                    config["llm"]["providers"][provider_name]["default_model"] = (
                        provider_data["default_model"]
                    )

        # Save updated config
        save_global_yaml_config(config)

        # Return updated config
        return await get_llm_config()
    except HTTPException:
        raise
    except ConfigError as exc:
        log_exception(logger, "Config error in update_llm_config", exc)
        raise HTTPException(status_code=500, detail=f"Failed to update LLM config: {str(exc)}")
    except Exception as exc:
        log_exception(logger, "Unexpected error in update_llm_config", exc)
        raise HTTPException(status_code=500, detail=f"Failed to update LLM config: {str(exc)}")

