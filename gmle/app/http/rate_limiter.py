"""Rate limiter implementation using token bucket algorithm with per-second, burst, and concurrency limits."""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any, Optional

from gmle.app.config.getter import get_rate_limit_config


class RateLimiter:
    """Token bucket rate limiter for API calls with per-second, burst, and concurrency limits."""

    def __init__(
        self,
        requests_per_second: float = 1.0,
        burst_limit: int = 2,
        requests_per_minute: int = 10,
        requests_per_hour: int = 500,
        concurrent_requests: int = 3,
        config: Optional[dict] = None,
    ):
        """Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second (can be fractional)
            burst_limit: Maximum requests in a short burst window (1 second)
            requests_per_minute: Maximum requests per minute
            requests_per_hour: Maximum requests per hour
            concurrent_requests: Maximum concurrent requests (semaphore)
            config: Optional config dict (for testing)
        """
        self.rps = requests_per_second
        self.burst_limit = burst_limit
        self.rpm = requests_per_minute
        self.rph = requests_per_hour
        self.max_concurrent = concurrent_requests
        
        # Token buckets
        self.second_tokens: float = float(burst_limit)  # Start with burst limit
        self.minute_tokens: float = float(requests_per_minute)
        self.hour_tokens: float = float(requests_per_hour)
        
        # Last update times
        self.last_second_update = time.time()
        self.last_minute_update = time.time()
        self.last_hour_update = time.time()
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
        # Request timestamps for burst tracking (sliding window)
        from collections import deque
        self.request_timestamps: deque = deque(maxlen=burst_limit * 2)
        
        # Request counter for hour bucket
        self.hour_request_count = 0
        self.hour_start_time = time.time()
        
        # Semaphore for concurrent requests
        self.concurrent_semaphore = threading.Semaphore(concurrent_requests)

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        
        # Refill second bucket (continuous refill based on RPS)
        elapsed_seconds = now - self.last_second_update
        if elapsed_seconds > 0:
            tokens_to_add = elapsed_seconds * self.rps
            self.second_tokens = min(self.burst_limit, self.second_tokens + tokens_to_add)
            self.last_second_update = now
        
        # Refill minute bucket
        elapsed_minutes = (now - self.last_minute_update) / 60.0
        if elapsed_minutes > 0:
            tokens_to_add = elapsed_minutes * self.rpm
            self.minute_tokens = min(self.rpm, self.minute_tokens + tokens_to_add)
            self.last_minute_update = now
        
        # Refill hour bucket (reset every hour)
        elapsed_hours = (now - self.hour_start_time) / 3600.0
        if elapsed_hours >= 1.0:
            # Reset hour bucket
            self.hour_tokens = self.rph
            self.hour_request_count = 0
            self.hour_start_time = now
        elif elapsed_hours > 0:
            # Partial refill based on elapsed time
            tokens_to_add = elapsed_hours * self.rph
            self.hour_tokens = min(self.rph, self.hour_tokens + tokens_to_add)

    def _check_burst_limit(self, now: float) -> bool:
        """Check if burst limit is exceeded.
        
        Args:
            now: Current timestamp
            
        Returns:
            True if burst limit is OK, False if exceeded
        """
        # Remove timestamps older than 1 second
        cutoff = now - 1.0
        while self.request_timestamps and self.request_timestamps[0] < cutoff:
            self.request_timestamps.popleft()
        
        # Check if we've exceeded burst limit in the last second
        if len(self.request_timestamps) >= self.burst_limit:
            return False
        
        return True

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire a token, waiting if necessary.

        Args:
            timeout: Maximum time to wait in seconds (None = wait indefinitely)

        Returns:
            True if token acquired, False if timeout
        """
        start_time = time.time()
        
        with self.lock:
            while True:
                now = time.time()
                self._refill_tokens()
                
                # Check all limits
                can_acquire = (
                    self.second_tokens >= 1.0
                    and self.minute_tokens >= 1.0
                    and self.hour_tokens >= 1.0
                    and self._check_burst_limit(now)
                )
                
                if can_acquire:
                    # Consume tokens
                    self.second_tokens -= 1.0
                    self.minute_tokens -= 1.0
                    self.hour_tokens -= 1.0
                    self.hour_request_count += 1
                    self.request_timestamps.append(now)
                    return True
                
                # Check timeout
                if timeout is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        return False
                
                # Wait a bit before checking again
                time.sleep(0.1)

    def acquire_with_concurrency(self, timeout: Optional[float] = None) -> bool:
        """Acquire token with concurrency limit (semaphore).
        
        This method combines rate limiting with concurrency control.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if acquired, False if timeout
        """
        # First, acquire rate limit token
        if not self.acquire(timeout=timeout):
            return False
        
        # Then, try to acquire semaphore
        if timeout is not None:
            # Acquire semaphore with timeout
            acquired = self.concurrent_semaphore.acquire(timeout=timeout)
            if not acquired:
                # Failed to acquire semaphore - we already consumed rate limit token
                # This is acceptable as the rate limit was passed
                return False
        else:
            self.concurrent_semaphore.acquire()
        
        return True

    def release_concurrency(self) -> None:
        """Release concurrency semaphore."""
        self.concurrent_semaphore.release()

    def get_status(self) -> dict:
        """Get current rate limiter status.

        Returns:
            Dict with token counts and next refill times
        """
        with self.lock:
            self._refill_tokens()
            
            # Calculate next refill times
            now = time.time()
            next_second_refill = max(0, 1.0 - (now - self.last_second_update))
            next_minute_refill = max(0, 60 - (now - self.last_minute_update))
            next_hour_refill = max(0, 3600 - (now - self.hour_start_time))
            
            # Count recent requests (burst window)
            cutoff = now - 1.0
            recent_requests = sum(1 for ts in self.request_timestamps if ts >= cutoff)
            
            return {
                "second_tokens": max(0, self.second_tokens),
                "minute_tokens": max(0, self.minute_tokens),
                "hour_tokens": max(0, self.hour_tokens),
                "requests_per_second": self.rps,
                "burst_limit": self.burst_limit,
                "requests_per_minute": self.rpm,
                "requests_per_hour": self.rph,
                "concurrent_requests": self.max_concurrent,
                "concurrent_available": self.concurrent_semaphore._value,
                "recent_requests_1s": recent_requests,
                "hour_request_count": self.hour_request_count,
                "next_second_refill_seconds": next_second_refill,
                "next_minute_refill_seconds": next_minute_refill,
                "next_hour_refill_seconds": next_hour_refill,
            }


# Global rate limiter instance (singleton pattern)
_global_rate_limiter: Any = None
_limiter_lock = threading.Lock()


def get_rate_limiter(config: Optional[dict] = None) -> Any:
    """Get global rate limiter instance.

    Args:
        config: Optional config dict (for testing)

    Returns:
        RateLimiter instance or NoOpRateLimiter
    """
    global _global_rate_limiter
    
    with _limiter_lock:
        if _global_rate_limiter is None:
            if config is None:
                rate_limit_config = get_rate_limit_config()
            else:
                rate_limit_config = config.get("rate_limit", {})
            
            if not rate_limit_config.get("enabled", True):
                # Return a no-op limiter that always allows requests
                class NoOpRateLimiter:
                    def acquire(self, timeout=None):
                        return True
                    def get_status(self):
                        return {
                            "minute_tokens": float("inf"),
                            "hour_tokens": float("inf"),
                            "requests_per_minute": float("inf"),
                            "requests_per_hour": float("inf"),
                            "hour_request_count": 0,
                            "next_minute_refill_seconds": 0,
                            "next_hour_refill_seconds": 0,
                        }
                _global_rate_limiter = NoOpRateLimiter()
                return _global_rate_limiter
            
            _global_rate_limiter = RateLimiter(
                requests_per_second=rate_limit_config.get("requests_per_second", 1.0),
                burst_limit=rate_limit_config.get("burst_limit", 2),
                requests_per_minute=rate_limit_config.get("requests_per_minute", 10),
                requests_per_hour=rate_limit_config.get("requests_per_hour", 500),
                concurrent_requests=rate_limit_config.get("concurrent_requests", 3),
                config=config,
            )
        
        return _global_rate_limiter


def reset_rate_limiter() -> None:
    """Reset global rate limiter (for testing)."""
    global _global_rate_limiter
    
    with _limiter_lock:
        _global_rate_limiter = None

