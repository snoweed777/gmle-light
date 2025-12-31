"""Unified API call gate with multi-layer rate limiting."""

from __future__ import annotations

import threading
from typing import Any, Callable, Dict, Optional

from gmle.app.config.getter import get_rate_limit_config
from gmle.app.http.rate_limiter import get_rate_limiter
from gmle.app.http.usage_tracker import get_usage_tracker
from gmle.app.infra.errors import InfraError


class UnifiedAPIGate:
    """Unified gate for all API calls with multi-layer rate limiting."""

    def __init__(self):
        """Initialize unified API gate."""
        self.usage_tracker = get_usage_tracker()
        self.rate_limiter = get_rate_limiter()

    def _get_call_type_limits(
        self,
        call_type: str,
        provider: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, int]:
        """Get limits for a specific call type and provider.

        Args:
            call_type: Type of call ("mcq_generation", "api_key_check", etc.)
            provider: LLM provider name
            config: Optional config dict

        Returns:
            Dict with limits: {
                "requests_per_minute": int,
                "requests_per_hour": int,
                "requests_per_day": int,
            }
        """
        rate_limit_config = get_rate_limit_config(config)
        
        # Default limits from global config
        default_rpm = rate_limit_config.get("requests_per_minute", 10)
        default_rph = rate_limit_config.get("requests_per_hour", 500)
        default_rpd = rate_limit_config.get("requests_per_day", 1400)
        
        # Get call type specific limits
        call_type_limits = rate_limit_config.get("call_type_limits", {})
        type_config = call_type_limits.get(call_type, {})
        
        # Get provider specific daily limit
        provider_limits = rate_limit_config.get("provider_daily_limits", {})
        provider_daily = provider_limits.get(provider)
        
        # Determine limits based on call type
        if call_type == "mcq_generation":
            # Critical calls: all limits apply
            return {
                "requests_per_minute": type_config.get("requests_per_minute", default_rpm),
                "requests_per_hour": type_config.get("requests_per_hour", default_rph),
                "requests_per_day": provider_daily if provider_daily is not None else type_config.get("requests_per_day", default_rpd),
            }
        elif call_type in ("api_key_check", "prerequisite_check"):
            # Diagnostic calls: relaxed limits, but still track daily
            return {
                "requests_per_minute": type_config.get("requests_per_minute", 60),  # Relaxed
                "requests_per_hour": type_config.get("requests_per_hour", 100),  # Relaxed
                "requests_per_day": type_config.get("requests_per_day", 50),  # Limited
            }
        elif call_type == "test":
            # Test calls: no limits, but track usage
            return {
                "requests_per_minute": 0,  # No limit (0 means unlimited)
                "requests_per_hour": 0,  # No limit (0 means unlimited)
                "requests_per_day": 0,  # No limit (0 means unlimited)
            }
        else:
            # Unknown call type: use defaults
            return {
                "requests_per_minute": default_rpm,
                "requests_per_hour": default_rph,
                "requests_per_day": default_rpd,
            }

    def call(
        self,
        call_type: str,
        provider: str,
        func: Callable,
        *args,
        config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Any:
        """Execute API call through unified gate.

        Args:
            call_type: Type of call ("mcq_generation", "api_key_check", etc.)
            provider: LLM provider name
            func: Function to call
            *args: Positional arguments for func
            config: Optional config dict
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            InfraError: If rate limit exceeded or other error
        """
        # Get limits for this call type
        limits = self._get_call_type_limits(call_type, provider, config)
        
        # Check daily/hourly limits via usage tracker
        # Only check if limits are not None
        if limits.get("requests_per_day") is not None or limits.get("requests_per_hour") is not None:
            can_acquire, reason = self.usage_tracker.can_acquire(call_type, provider, limits)
            if not can_acquire:
                raise InfraError(f"API call blocked: {reason}")
        
        # Check second/minute/hour limits via rate limiter (only for critical calls)
        if call_type == "mcq_generation" and limits.get("requests_per_minute") is not None:
            # Acquire rate limit token with concurrency control
            if not self.rate_limiter.acquire_with_concurrency(timeout=300):
                raise InfraError("Rate limit: Could not acquire token within timeout period")
            
            # We'll release concurrency semaphore after API call completes
            concurrency_acquired = True
        else:
            concurrency_acquired = False
        
        # Execute API call
        try:
            result = func(*args, config=config, **kwargs)
            # Record successful call
            self.usage_tracker.record_call(call_type, provider, success=True)
            return result
        except Exception:
            # Record failed call (but don't count towards limits)
            self.usage_tracker.record_call(call_type, provider, success=False)
            raise
        finally:
            # Release concurrency semaphore if acquired
            if concurrency_acquired:
                self.rate_limiter.release_concurrency()


# Global instance
_global_api_gate: Optional[UnifiedAPIGate] = None
_gate_lock = threading.Lock()


def get_unified_api_gate() -> UnifiedAPIGate:
    """Get global unified API gate instance.

    Returns:
        UnifiedAPIGate instance
    """
    global _global_api_gate
    
    with _gate_lock:
        if _global_api_gate is None:
            _global_api_gate = UnifiedAPIGate()
        
        return _global_api_gate


def reset_unified_api_gate() -> None:
    """Reset global API gate (for testing)."""
    global _global_api_gate
    
    with _gate_lock:
        _global_api_gate = None

