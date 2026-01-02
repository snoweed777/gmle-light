"""HuggingFace Inference API client."""

from __future__ import annotations

import os
from typing import Any, Dict

from dotenv import load_dotenv

from gmle.app.config.getter import get_llm_config
from gmle.app.http.base import request
from gmle.app.infra.errors import InfraError

# Load .env file
load_dotenv()


def _check_api_key_status_impl(config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Internal implementation of API key check (without rate limiting)."""
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        return {
            "valid": False,
            "error": "HUGGINGFACE_API_KEY not set",
            "key_type": None,
            "has_quota": False,
        }
    
    # Make a minimal test request using OpenAI-compatible endpoint
    import httpx
    client = httpx.Client(timeout=30.0)
    try:
        # Use HuggingFace Inference Providers endpoint (OpenAI-compatible)
        api_url = "https://router.huggingface.co/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        # Minimal test request
        payload = {
            "model": "meta-llama/Llama-3.2-1B-Instruct",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 10,
        }
        
        resp = client.post(api_url, headers=headers, json=payload)
        
        if resp.status_code == 200:
            return {
                "valid": True,
                "error": None,
                "key_type": "free",
                "has_quota": True,
            }
        elif resp.status_code == 429:
            # Rate limit
            return {
                "valid": True,
                "error": "Rate limit reached",
                "key_type": "free",
                "has_quota": False,
                "error_detail": resp.text[:200],
            }
        elif resp.status_code in (401, 403):
            return {
                "valid": False,
                "error": f"Authentication failed: {resp.status_code}",
                "key_type": None,
                "has_quota": False,
            }
        else:
            return {
                "valid": False,
                "error": f"Unexpected status: {resp.status_code}",
                "key_type": None,
                "has_quota": False,
                "error_detail": resp.text[:200],
            }
    except Exception as e:
        return {
            "valid": False,
            "error": f"Failed to check API key: {str(e)}",
            "key_type": None,
            "has_quota": False,
        }
    finally:
        client.close()


def check_api_key_status(config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Check HuggingFace API key status through unified gate."""
    from gmle.app.http.api_gate import get_unified_api_gate
    from gmle.app.config.getter import get_llm_config
    
    llm_config = get_llm_config(config)
    provider = llm_config.get("active_provider", "huggingface")
    
    # Check if we can make the call (but don't block if we can't)
    gate = get_unified_api_gate()
    try:
        result: Any = gate.call(
            call_type="api_key_check",
            provider=provider,
            func=_check_api_key_status_impl,
            config=config,
        )
        return result  # type: ignore[no-any-return]
    except InfraError as e:
        # If blocked by rate limit, return error status
        if "blocked" in str(e).lower() or "limit" in str(e).lower():
            return {
                "valid": True,
                "error": f"Rate limit check blocked: {str(e)}",
                "key_type": "free",
                "has_quota": False,
            }
        # Otherwise, try without gate (fallback)
        return _check_api_key_status_impl(config)


def _chat_completions_impl(payload: Dict[str, Any], config: Dict[str, Any] | None = None) -> Any:
    """Internal implementation of HuggingFace API call (without rate limiting)."""
    llm_config = get_llm_config(config)
    provider_config = llm_config.get("provider_config", {})
    default_model = provider_config.get("default_model") or "meta-llama/Llama-3.2-3B-Instruct"
    
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        raise InfraError("HUGGINGFACE_API_KEY not set")
    
    # Extract messages from payload
    messages = payload.get("messages", [])
    if not messages:
        raise InfraError("messages array is required")
    
    # Extract model from payload or use config default
    model = payload.get("model", default_model)
    
    # HuggingFace Inference Providers endpoint (OpenAI-compatible)
    api_url = "https://router.huggingface.co/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    # OpenAI-compatible payload
    hf_payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 2000,
        "temperature": 0.7,
    }
    
    response = request("POST", api_url, headers=headers, json=hf_payload, config=config)
    
    # OpenAI-compatible response format
    from gmle.app.http.json_parser import parse_llm_response
    return parse_llm_response(response)


def chat_completions(payload: Dict[str, Any], config: Dict[str, Any] | None = None) -> Any:
    """Call HuggingFace Inference API through unified gate."""
    from gmle.app.http.api_gate import get_unified_api_gate
    from gmle.app.config.getter import get_llm_config
    
    llm_config = get_llm_config(config)
    provider = llm_config.get("active_provider", "huggingface")
    
    gate = get_unified_api_gate()
    return gate.call(
        call_type="mcq_generation",
        provider=provider,
        func=_chat_completions_impl,
        payload=payload,
        config=config,
    )

