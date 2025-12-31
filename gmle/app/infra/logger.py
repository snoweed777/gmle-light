"""Structured logger setup with file output and CLI detection."""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from logging.handlers import TimedRotatingFileHandler


def _is_cli_execution() -> bool:
    """Check if running as CLI (via __main__)."""
    if len(sys.argv) == 0:
        return False
    main_module = sys.modules.get("__main__")
    if main_module is None:
        return False
    main_file = getattr(main_module, "__file__", None)
    if main_file is None:
        return False
    main_file_str = str(main_file)
    return "cli" in main_file_str or "main.py" in main_file_str or "gmle.app.cli" in main_file_str


def _sanitize_sensitive_data(data: Any) -> Any:
    """Replace sensitive data with ***."""
    if isinstance(data, dict):
        sanitized = {}
        sensitive_keys = {"api_key", "token", "password", "secret", "auth"}
        for key, value in data.items():
            if any(sk in key.lower() for sk in sensitive_keys):
                sanitized[key] = "***"
            else:
                sanitized[key] = _sanitize_sensitive_data(value)
        return sanitized
    if isinstance(data, list):
        return [_sanitize_sensitive_data(item) for item in data]
    if isinstance(data, str):
        # Check for common API key patterns
        if len(data) > 20 and any(c in data for c in ["sk-", "Bearer ", "Token"]):
            return "***"
    return data


class _KVFormatter(logging.Formatter):
    def __init__(self, *, human: bool = False) -> None:
        super().__init__()
        self.human = human

    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover
        """Format log record as JSON or human-readable."""
        payload: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        
        # Add extra fields
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            sanitized_fields = _sanitize_sensitive_data(record.extra_fields)
            payload.update(sanitized_fields)
        
        # Add traceback for errors
        if record.exc_info:
            payload["traceback"] = self.formatException(record.exc_info)
        
        if self.human:
            parts = []
            parts.append(f"[{payload['timestamp']}] {payload['level']}: {payload['message']}")
            for key, value in payload.items():
                if key not in {"timestamp", "level", "message"}:
                    if key == "traceback":
                        parts.append(f"\n{value}")
                    else:
                        parts.append(f"{key}={value}")
            return " ".join(parts)
        
        return json.dumps(payload, ensure_ascii=False)


def _get_log_file_path(space_id: Optional[str] = None) -> Optional[Path]:
    """Get log file path from environment or default location."""
    log_file = os.getenv("GMLE_LOG_FILE")
    if log_file:
        return Path(log_file)
    
    if space_id:
        # Default: data/<space>/logs/gmle-<date>.log
        root = Path.cwd()
        log_dir = root / "data" / space_id / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        from .time_id import today_str
        return log_dir / f"gmle-{today_str()}.log"
    
    return None


def get_logger(name: str = "gmle", space_id: Optional[str] = None) -> logging.Logger:
    """Return configured logger with file output and CLI detection."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    # Determine log format from environment or CLI detection
    log_format_env = os.getenv("GMLE_LOG_FORMAT", "").lower()
    is_cli = _is_cli_execution()
    human_readable = log_format_env == "human" or (is_cli and log_format_env != "json")
    
    # Determine log level from environment
    log_level_str = os.getenv("GMLE_LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Console handler (human-readable for CLI, JSON otherwise)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(_KVFormatter(human=human_readable))
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)
    
    # File handler (always JSON)
    log_file = _get_log_file_path(space_id)
    if log_file:
        file_handler = TimedRotatingFileHandler(
            str(log_file),
            when="midnight",
            interval=1,
            backupCount=int(os.getenv("GMLE_LOG_ROTATION", "30")),
            encoding="utf-8",
        )
        file_handler.setFormatter(_KVFormatter(human=False))
        file_handler.setLevel(logging.DEBUG)  # File always has DEBUG level
        logger.addHandler(file_handler)
    
    logger.setLevel(log_level)
    logger.propagate = False
    return logger


def with_fields(logger: logging.Logger, **fields: Any) -> Dict[str, Any]:
    """Helper to attach extra fields when logging."""
    return {"extra": {"extra_fields": fields}}


def log_exception(logger: logging.Logger, message: str, exc: Exception, **extra: Any) -> None:
    """Log exception with traceback and extra fields."""
    logger.error(
        message,
        exc_info=True,
        extra={"extra_fields": {**extra, "exception_type": type(exc).__name__}},
    )
