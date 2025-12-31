"""Global API usage tracker with persistence and file locking."""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import orjson

from gmle.app.infra.errors import InfraError
from gmle.app.infra.logger import get_logger, log_exception


class GlobalUsageTracker:
    """Global API usage tracker with file-based persistence and process-safe locking."""

    def __init__(self, usage_file: Path):
        """Initialize usage tracker.

        Args:
            usage_file: Path to usage tracking file
        """
        self.usage_file = usage_file
        self.lock_file = usage_file.with_suffix('.lock')
        self.lock = threading.Lock()
        
        # Ensure directory exists
        self.usage_file.parent.mkdir(parents=True, exist_ok=True)

    def _acquire_file_lock(self):
        """Acquire file lock for process-safe operations."""
        import fcntl
        
        class FileLock:
            def __init__(self, lock_file: Path):
                self.lock_file = lock_file
                self.fd = None
            
            def __enter__(self):
                self.fd = open(self.lock_file, 'w')
                fcntl.flock(self.fd.fileno(), fcntl.LOCK_EX)
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.fd:
                    fcntl.flock(self.fd.fileno(), fcntl.LOCK_UN)
                    self.fd.close()
        
        return FileLock(self.lock_file)

    def _get_utc_date(self) -> str:
        """Get current UTC date string (YYYY-MM-DD)."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _get_utc_hour(self) -> str:
        """Get current UTC hour string (YYYY-MM-DDTHH)."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H")

    def _load_usage(self) -> Dict[str, Any]:
        """Load usage data from file."""
        logger = get_logger()
        
        if not self.usage_file.exists():
            return {
                "version": "1.0",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "daily_usage": {},
                "hourly_usage": {},
                "metadata": {
                    "last_reset_utc": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
                },
            }
        
        try:
            with self.usage_file.open("rb") as f:
                data = orjson.loads(f.read())
            
            # Validate structure
            if not isinstance(data, dict):
                raise ValueError("Invalid usage file format")
            
            # Ensure required fields
            if "daily_usage" not in data:
                data["daily_usage"] = {}
            if "hourly_usage" not in data:
                data["hourly_usage"] = {}
            if "metadata" not in data:
                data["metadata"] = {}
            
            return data
        except (orjson.JSONDecodeError, ValueError, IOError) as e:
            # File corrupted or invalid - reset to empty
            log_exception(
                logger,
                "Failed to load usage data, resetting",
                e,
                usage_file=str(self.usage_file),
            )
            return {
                "version": "1.0",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "daily_usage": {},
                "hourly_usage": {},
                "metadata": {
                    "last_reset_utc": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
                    "reset_reason": f"File corruption: {str(e)}",
                },
            }

    def _save_usage(self, usage: Dict[str, Any]) -> None:
        """Save usage data atomically."""
        logger = get_logger()
        
        # Atomic write: write to temp file, then rename
        temp_file = self.usage_file.with_suffix('.tmp')
        
        try:
            usage["last_updated"] = datetime.now(timezone.utc).isoformat()
            
            with temp_file.open("wb") as f:
                f.write(orjson.dumps(usage, option=orjson.OPT_INDENT_2))
            
            # Atomic rename
            temp_file.replace(self.usage_file)
        except IOError as e:
            # Clean up temp file on error
            if temp_file.exists():
                temp_file.unlink()
            log_exception(
                logger,
                "Failed to save usage data",
                e,
                usage_file=str(self.usage_file),
            )
            raise InfraError(f"Failed to save usage data: {e}") from e

    def _reset_daily_usage_if_needed(self, usage: Dict[str, Any]) -> bool:
        """Reset daily usage if UTC date changed. Returns True if reset occurred."""
        current_date = self._get_utc_date()
        last_reset_str = usage.get("metadata", {}).get("last_reset_utc", "")
        
        if last_reset_str:
            try:
                last_reset = datetime.fromisoformat(last_reset_str.replace('Z', '+00:00'))
                last_reset_date = last_reset.strftime("%Y-%m-%d")
                
                if current_date != last_reset_date:
                    # Date changed - reset daily usage
                    usage["daily_usage"] = {}
                    usage["hourly_usage"] = {}
                    usage["metadata"]["last_reset_utc"] = datetime.now(timezone.utc).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    ).isoformat()
                    return True
            except (ValueError, AttributeError):
                # Invalid date format - reset
                usage["daily_usage"] = {}
                usage["hourly_usage"] = {}
                usage["metadata"]["last_reset_utc"] = datetime.now(timezone.utc).replace(
                    hour=0, minute=0, second=0, microsecond=0
                ).isoformat()
                return True
        else:
            # No reset time recorded - initialize
            usage["metadata"]["last_reset_utc"] = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            ).isoformat()
        
        return False

    def record_call(
        self,
        call_type: str,
        provider: str,
        success: bool = True,
    ) -> None:
        """Record an API call.

        Args:
            call_type: Type of call ("mcq_generation", "api_key_check", etc.)
            provider: LLM provider name ("gemini", "cohere", etc.)
            success: Whether the call was successful
        """
        with self.lock:
            with self._acquire_file_lock():
                usage = self._load_usage()
                
                # Reset daily usage if date changed
                self._reset_daily_usage_if_needed(usage)
                
                current_date = self._get_utc_date()
                current_hour = self._get_utc_hour()
                
                # Initialize date entry if needed
                if current_date not in usage["daily_usage"]:
                    usage["daily_usage"][current_date] = {}
                
                if provider not in usage["daily_usage"][current_date]:
                    usage["daily_usage"][current_date][provider] = {
                        "mcq_generation": 0,
                        "api_key_check": 0,
                        "prerequisite_check": 0,
                        "test": 0,
                        "total": 0,
                    }
                
                # Initialize hour entry if needed
                if current_hour not in usage["hourly_usage"]:
                    usage["hourly_usage"][current_hour] = {}
                
                if provider not in usage["hourly_usage"][current_hour]:
                    usage["hourly_usage"][current_hour][provider] = {
                        "mcq_generation": 0,
                        "api_key_check": 0,
                        "prerequisite_check": 0,
                        "test": 0,
                        "total": 0,
                    }
                
                # Only count successful calls
                if success:
                    # Increment counters (use setdefault for efficiency)
                    daily_provider = usage["daily_usage"][current_date][provider]
                    daily_provider.setdefault(call_type, 0)
                    daily_provider[call_type] += 1
                    daily_provider["total"] += 1
                    
                    hourly_provider = usage["hourly_usage"][current_hour][provider]
                    hourly_provider.setdefault(call_type, 0)
                    hourly_provider[call_type] += 1
                    hourly_provider["total"] += 1
                
                self._save_usage(usage)

    def get_usage(
        self,
        provider: str,
        date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get usage statistics for a provider.

        Args:
            provider: LLM provider name
            date: Date string (YYYY-MM-DD), defaults to today

        Returns:
            Dict with usage statistics
        """
        with self.lock:
            with self._acquire_file_lock():
                usage = self._load_usage()
                self._reset_daily_usage_if_needed(usage)
                
                if date is None:
                    date = self._get_utc_date()
                
                daily = usage["daily_usage"].get(date, {}).get(provider, {
                    "mcq_generation": 0,
                    "api_key_check": 0,
                    "prerequisite_check": 0,
                    "test": 0,
                    "total": 0,
                })
                
                current_hour = self._get_utc_hour()
                hourly = usage["hourly_usage"].get(current_hour, {}).get(provider, {
                    "mcq_generation": 0,
                    "api_key_check": 0,
                    "prerequisite_check": 0,
                    "test": 0,
                    "total": 0,
                })
                
                return {
                    "daily": daily,
                    "hourly": hourly,
                    "date": date,
                    "hour": current_hour,
                }

    def can_acquire(
        self,
        call_type: str,
        provider: str,
        limits: Dict[str, int],
    ) -> Tuple[bool, str]:
        """Check if API call can be made.

        Args:
            call_type: Type of call
            provider: LLM provider name
            limits: Dict with limits for this call type
                {
                    "requests_per_minute": int,
                    "requests_per_hour": int,
                    "requests_per_day": int,
                }

        Returns:
            Tuple of (can_acquire, reason)
        """
        with self.lock:
            with self._acquire_file_lock():
                usage = self._load_usage()
                self._reset_daily_usage_if_needed(usage)
                
                current_date = self._get_utc_date()
                current_hour = self._get_utc_hour()
                
                # Get current usage
                daily_usage = usage["daily_usage"].get(current_date, {}).get(provider, {})
                hourly_usage = usage["hourly_usage"].get(current_hour, {}).get(provider, {})
                
                daily_total = daily_usage.get("total", 0)
                hourly_total = hourly_usage.get("total", 0)
                call_type_daily = daily_usage.get(call_type, 0)
                call_type_hourly = hourly_usage.get(call_type, 0)
                
                # Check daily limit
                daily_limit = limits.get("requests_per_day")
                if daily_limit is not None:
                    if daily_total >= daily_limit:
                        return False, f"Daily limit reached: {daily_total}/{daily_limit}"
                    if call_type_daily >= daily_limit:
                        return False, f"Daily limit reached for {call_type}: {call_type_daily}/{daily_limit}"
                
                # Check hourly limit
                hourly_limit = limits.get("requests_per_hour")
                if hourly_limit is not None:
                    if hourly_total >= hourly_limit:
                        return False, f"Hourly limit reached: {hourly_total}/{hourly_limit}"
                    if call_type_hourly >= hourly_limit:
                        return False, f"Hourly limit reached for {call_type}: {call_type_hourly}/{hourly_limit}"
                
                # Note: Minute limit is checked by RateLimiter, not here
                
                return True, "OK"


# Global instance
_global_usage_tracker: Optional[GlobalUsageTracker] = None
_tracker_lock = threading.Lock()


def get_usage_tracker(usage_file: Optional[Path] = None) -> GlobalUsageTracker:
    """Get global usage tracker instance.

    Args:
        usage_file: Optional path to usage file (for testing)

    Returns:
        GlobalUsageTracker instance
    """
    global _global_usage_tracker
    
    with _tracker_lock:
        if _global_usage_tracker is None:
            if usage_file is None:
                # Default: data/.rate_limit_usage.json
                from pathlib import Path
                usage_file = Path("data/.rate_limit_usage.json")
            
            _global_usage_tracker = GlobalUsageTracker(usage_file)
        
        return _global_usage_tracker


def reset_usage_tracker() -> None:
    """Reset global usage tracker (for testing)."""
    global _global_usage_tracker
    
    with _tracker_lock:
        _global_usage_tracker = None

