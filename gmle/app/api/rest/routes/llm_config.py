"""LLM configuration endpoints."""

from __future__ import annotations

import os
import shutil
from datetime import datetime
from typing import Any, Dict

import yaml
from fastapi import APIRouter, HTTPException

from gmle.app.api.rest.models import (
    LLMConfigResponse,
    LLMConfigUpdateRequest,
    LLMProviderInfo,
)
from gmle.app.config.env_paths import get_config_dir
from gmle.app.config.secrets import SecretsManager

router = APIRouter(prefix="/config/llm", tags=["llm_config"])


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

    # Create backup if file exists
    if config_file.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = config_file.with_suffix(f".{timestamp}.backup")
        shutil.copy2(config_file, backup_file)

    # Save updated config
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


@router.get("", response_model=LLMConfigResponse)
async def get_llm_config() -> LLMConfigResponse:
    """Get LLM configuration."""
    config = _load_global_config()
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


@router.put("", response_model=LLMConfigResponse)
async def update_llm_config(
    request: LLMConfigUpdateRequest,
) -> LLMConfigResponse:
    """Update LLM configuration."""
    config = _load_global_config()

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
    _save_global_config(config)

    # Return updated config
    return await get_llm_config()

