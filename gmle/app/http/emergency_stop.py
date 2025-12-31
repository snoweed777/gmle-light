"""Emergency stop for API calls (small independent module)."""

from __future__ import annotations

import threading

_emergency_stop: bool = False
_lock = threading.Lock()


def is_emergency_stopped() -> bool:
    """Check if emergency stop is active.
    
    Returns:
        True if emergency stop is enabled
    """
    with _lock:
        return _emergency_stop


def set_emergency_stop(enabled: bool) -> None:
    """Enable/disable emergency stop.
    
    Args:
        enabled: True to enable emergency stop, False to disable
    """
    global _emergency_stop
    with _lock:
        _emergency_stop = enabled


def check_emergency_stop() -> None:
    """Raise error if emergency stop is active.
    
    Raises:
        InfraError: If emergency stop is enabled
    """
    if is_emergency_stopped():
        from gmle.app.infra.errors import InfraError
        raise InfraError(
            "EMERGENCY_STOP: API calls temporarily disabled",
            code="EMERGENCY_STOP",
            user_message="API呼び出しが一時的に無効化されています",
            retryable=False,
        )

