"""Unified LLM client with provider abstraction."""

from __future__ import annotations

from typing import Any, Dict

from gmle.app.config.getter import get_llm_config
from gmle.app.infra.errors import InfraError


def chat_completions(payload: Dict[str, Any], config: Dict[str, Any] | None = None) -> Any:
    """Call LLM chat completions using active provider."""
    llm_config = get_llm_config(config)
    active_provider = llm_config.get("active_provider", "cohere")
    
    if active_provider == "cohere":
        from gmle.app.http.cohere_client import chat_completions as cohere_chat_completions
        return cohere_chat_completions(payload, config=config)
    elif active_provider == "gemini":
        from gmle.app.http.gemini_client import chat_completions as gemini_chat_completions
        return gemini_chat_completions(payload, config=config)
    elif active_provider == "groq":
        from gmle.app.http.groq_client import chat_completions as groq_chat_completions
        return groq_chat_completions(payload, config=config)
    else:
        raise InfraError(f"Unknown LLM provider: {active_provider}")

