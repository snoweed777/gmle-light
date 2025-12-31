"""Common API key checking utilities."""

from __future__ import annotations

from typing import Any, Dict

from gmle.app.config.getter import get_llm_config


def check_api_key_for_provider(provider: str, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Check API key status for a specific provider.
    
    Args:
        provider: LLM provider name ("cohere", "gemini", "groq")
        config: Optional config dict
        
    Returns:
        Dict with API key status:
        {
            "valid": bool,
            "error": str | None,
            "key_type": str | None,
            "has_quota": bool,
        }
    """
    if provider == "cohere":
        from gmle.app.http.cohere_client import check_api_key_status
        return check_api_key_status(config=config)
    elif provider == "gemini":
        from gmle.app.http.gemini_client import check_api_key_status
        return check_api_key_status(config=config)
    elif provider == "groq":
        from gmle.app.http.groq_client import check_api_key_status
        return check_api_key_status(config=config)
    else:
        return {
            "valid": False,
            "error": f"Unknown provider: {provider}",
            "key_type": None,
            "has_quota": False,
        }


def check_active_provider_api_key(config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Check API key status for the active LLM provider.
    
    Args:
        config: Optional config dict
        
    Returns:
        Dict with API key status and provider name
    """
    llm_config = get_llm_config(config)
    active_provider = llm_config.get("active_provider", "cohere")
    
    api_status = check_api_key_for_provider(active_provider, config=config)
    api_status["provider"] = active_provider
    
    return api_status

