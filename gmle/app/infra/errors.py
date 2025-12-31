"""Domain-specific exception categories with structured error support."""

from __future__ import annotations

from typing import Any, Dict


class GMLEError(Exception):
    """Base exception with structured error information."""
    
    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        user_message: str | None = None,
        details: Dict[str, Any] | None = None,
        retryable: bool = False,
    ):
        super().__init__(message)
        self.code = code or self.__class__.__name__.upper()
        self.user_message = user_message or message
        self.details = details or {}
        self.retryable = retryable
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "error": self.user_message,
            "code": self.code,
            "details": self.details,
            "retryable": self.retryable,
        }


class ConfigError(GMLEError):
    """Configuration related failure."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            code=kwargs.pop("code", "CONFIG_ERROR"),
            user_message=kwargs.pop("user_message", f"設定エラー: {message}"),
            **kwargs
        )


class InfraError(GMLEError):
    """Infrastructure (I/O, lock, OS) failure."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            code=kwargs.pop("code", "INFRA_ERROR"),
            user_message=kwargs.pop("user_message", f"インフラエラー: {message}"),
            retryable=kwargs.pop("retryable", True),
            **kwargs
        )


class AnkiError(GMLEError):
    """AnkiConnect failure."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            code=kwargs.pop("code", "ANKI_ERROR"),
            user_message=kwargs.pop("user_message", f"Ankiエラー: {message}"),
            retryable=kwargs.pop("retryable", True),
            **kwargs
        )


class SOTError(GMLEError):
    """Source of Truth (items/ledger) failure."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            code=kwargs.pop("code", "SOT_ERROR"),
            user_message=kwargs.pop("user_message", f"データエラー: {message}"),
            retryable=kwargs.pop("retryable", False),
            **kwargs
        )


class CycleError(GMLEError):
    """Cycle selection/apply failure."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            code=kwargs.pop("code", "CYCLE_ERROR"),
            user_message=kwargs.pop("user_message", f"サイクルエラー: {message}"),
            retryable=kwargs.pop("retryable", False),
            **kwargs
        )


class DegradeTrigger(GMLEError):
    """Triggers Safe-Degrade path."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            code=kwargs.pop("code", "DEGRADE_TRIGGER"),
            user_message=kwargs.pop("user_message", f"Degradeモード: {message}"),
            retryable=kwargs.pop("retryable", False),
            **kwargs
        )
