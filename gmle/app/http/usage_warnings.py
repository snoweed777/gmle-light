"""Generate usage warnings (small independent module)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from gmle.app.http.usage_tracker import get_usage_tracker


def get_usage_warnings(
    provider: str,
    provider_limit: int | None = None,
    threshold: float = 0.9,
) -> List[str]:
    """Get warnings for approaching limits.
    
    Args:
        provider: LLM provider name
        provider_limit: Daily limit for provider
        threshold: Warning threshold (0.0-1.0)
    
    Returns:
        List of warning messages
    """
    if not provider_limit:
        return []
    
    warnings = []
    usage_tracker = get_usage_tracker()
    usage = usage_tracker.get_usage(provider)
    
    daily_used = usage["daily"]["total"]
    daily_percent = (daily_used / provider_limit) * 100
    
    if daily_percent >= 90:
        warnings.append("CRITICAL: Daily limit nearly reached")
    elif daily_percent >= 75:
        warnings.append("WARNING: Daily limit at 75%")
    
    # Predictive warnings
    current_hour = datetime.now().hour
    hours_remaining = max(1, 24 - current_hour)
    hourly_rate = usage["hourly"]["total"] / max(1, current_hour)
    predicted_daily = daily_used + (hourly_rate * hours_remaining)
    predicted_percent = (predicted_daily / provider_limit) * 100
    
    if predicted_percent >= 100:
        warnings.append("CRITICAL: Predicted to exceed daily limit")
    elif predicted_percent >= 90:
        warnings.append("WARNING: Predicted to reach 90% of daily limit")
    
    return warnings

