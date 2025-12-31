"""Config getter utilities."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from gmle.app.config.yaml_io import load_global_yaml_config


_config_cache: Optional[Dict[str, Any]] = None


def _get_config_with_fallback(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get config from parameter, cache, or file.
    
    Args:
        config: Optional config dict
        
    Returns:
        Config dictionary
    """
    if config is not None:
        return config
    
    if _config_cache is not None:
        return _config_cache
    
    # Fallback: try to load from file
    try:
        return load_global_yaml_config()
    except Exception:
        # If file loading fails, return empty dict
        return {}


def set_config(config: Dict[str, Any]) -> None:
    """Set global config cache."""
    global _config_cache
    _config_cache = config


def get_config() -> Optional[Dict[str, Any]]:
    """Get global config cache."""
    return _config_cache


def get_api_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get API configuration."""
    cfg = config or _config_cache or {}
    api_cfg = cfg.get("api", {})
    
    # Cohere config
    cohere_cfg = api_cfg.get("cohere", {})
    cohere_api_url = cohere_cfg.get("api_url") or os.getenv("COHERE_API_URL") or "https://api.cohere.ai/v1/chat"
    cohere_model = cohere_cfg.get("model") or "command-a-03-2025"
    
    # Readwise config
    readwise_cfg = api_cfg.get("readwise", {})
    readwise_api_url = readwise_cfg.get("api_url") or "https://readwise.io/api/v2/highlights/"
    
    # Anki config
    anki_cfg = api_cfg.get("anki", {})
    anki_connect_url = anki_cfg.get("connect_url") or os.getenv("ANKI_CONNECT_URL") or "http://127.0.0.1:8765"
    anki_connect_version = anki_cfg.get("connect_version") or 6
    anki_auto_sync = anki_cfg.get("auto_sync", True)
    
    return {
        "cohere": {
            "api_url": cohere_api_url,
            "model": cohere_model,
        },
        "readwise": {
            "api_url": readwise_api_url,
        },
        "anki": {
            "connect_url": anki_connect_url,
            "connect_version": anki_connect_version,
            "auto_sync": anki_auto_sync,
        },
    }


def get_anki_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get Anki configuration."""
    cfg = config or _config_cache or {}
    anki_cfg = cfg.get("anki", {})
    
    note_type_name = anki_cfg.get("note_type_name") or "GMLE_MCQA"
    deck_bank_prefix = anki_cfg.get("deck_bank_prefix") or "GMLE::Bank::"
    
    return {
        "note_type_name": note_type_name,
        "deck_bank_prefix": deck_bank_prefix,
    }


def get_http_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get HTTP configuration."""
    cfg = config or _config_cache or {}
    http_cfg = cfg.get("http", {})
    
    timeout = http_cfg.get("timeout") or 30.0
    max_retries = http_cfg.get("max_retries") or 3
    retry_backoff_base = http_cfg.get("retry_backoff_base") or 2
    
    return {
        "timeout": timeout,
        "max_retries": max_retries,
        "retry_backoff_base": retry_backoff_base,
    }


def get_rate_limit_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get rate limit configuration."""
    cfg = _get_config_with_fallback(config)
    rate_limit_cfg = cfg.get("rate_limit", {})
    
    enabled = rate_limit_cfg.get("enabled", True)
    requests_per_second = rate_limit_cfg.get("requests_per_second", 1.0)
    burst_limit = rate_limit_cfg.get("burst_limit", 2)
    requests_per_minute = rate_limit_cfg.get("requests_per_minute") or 10
    requests_per_hour = rate_limit_cfg.get("requests_per_hour") or 500
    requests_per_day = rate_limit_cfg.get("requests_per_day") or 1400
    concurrent_requests = rate_limit_cfg.get("concurrent_requests", 3)
    cooldown_seconds = rate_limit_cfg.get("cooldown_seconds") or 60
    
    # Call type specific limits
    call_type_limits = rate_limit_cfg.get("call_type_limits", {})
    
    # Provider specific daily limits
    provider_daily_limits = rate_limit_cfg.get("provider_daily_limits", {})
    
    return {
        "enabled": enabled,
        "requests_per_second": requests_per_second,
        "burst_limit": burst_limit,
        "requests_per_minute": requests_per_minute,
        "requests_per_hour": requests_per_hour,
        "requests_per_day": requests_per_day,
        "concurrent_requests": concurrent_requests,
        "cooldown_seconds": cooldown_seconds,
        "call_type_limits": call_type_limits,
        "provider_daily_limits": provider_daily_limits,
    }


def get_lock_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get lock configuration."""
    cfg = config or _config_cache or {}
    lock_cfg = cfg.get("lock", {})
    
    stale_seconds = lock_cfg.get("stale_seconds") or 3600
    
    return {
        "stale_seconds": stale_seconds,
    }


def get_ingest_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get ingest configuration."""
    cfg = config or _config_cache or {}
    ingest_cfg = cfg.get("ingest", {})
    params = cfg.get("params", {})
    
    excerpt_min = ingest_cfg.get("excerpt_min") or params.get("excerpt_min") or 200
    excerpt_max = ingest_cfg.get("excerpt_max") or params.get("excerpt_max") or 800
    quarantine_min_length = ingest_cfg.get("quarantine_min_length") or excerpt_min
    
    return {
        "excerpt_min": excerpt_min,
        "excerpt_max": excerpt_max,
        "quarantine_min_length": quarantine_min_length,
    }


def get_llm_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get LLM configuration."""
    cfg = _get_config_with_fallback(config)
    llm_cfg = cfg.get("llm", {})
    
    active_provider = llm_cfg.get("active_provider", "cohere")
    providers_cfg = llm_cfg.get("providers", {})
    
    # Get provider-specific config
    provider_config = {}
    if active_provider in providers_cfg:
        provider_config = providers_cfg[active_provider]
    
    return {
        "active_provider": active_provider,
        "provider_config": provider_config,
    }

