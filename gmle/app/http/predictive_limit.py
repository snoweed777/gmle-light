"""Predictive rate limit checker (small independent module)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Tuple

from gmle.app.http.usage_tracker import get_usage_tracker


def check_predictive_limit(
    provider: str,
    provider_limit: int,
    threshold: float = 0.9,
    config: Dict[str, Any] | None = None,
) -> Tuple[bool, str]:
    """Check if predicted usage will exceed limit.
    
    Args:
        provider: LLM provider name
        provider_limit: Daily limit for provider
        threshold: Warning threshold (0.0-1.0)
        config: Optional config dict
    
    Returns:
        Tuple of (can_proceed, reason)
    """
    if not provider_limit:
        return True, "OK"
    
    usage_tracker = get_usage_tracker()
    usage = usage_tracker.get_usage(provider)
    
    daily_used = usage["daily"]["total"]
    current_hour = datetime.now().hour
    hours_remaining = max(1, 24 - current_hour)
    
    # Calculate hourly rate (requests per hour)
    hourly_rate = usage["hourly"]["total"] / max(1, current_hour)
    predicted_daily = daily_used + (hourly_rate * hours_remaining)
    
    if predicted_daily >= provider_limit * threshold:
        return False, (
            f"Predicted daily usage ({predicted_daily:.0f}) "
            f"will exceed {threshold*100:.0f}% of limit ({provider_limit})"
        )
    
    return True, "OK"

