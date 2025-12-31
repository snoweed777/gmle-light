"""Paths and deck resolution check (Sx1-Sx4)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from gmle.app.infra.errors import ConfigError
from gmle.app.infra.logger import get_logger


def check_paths_deck(paths: Dict[str, Any], space_id: str, deck_bank: str) -> None:
    """Check paths and deck resolution (Sx1-Sx4)."""
    logger = get_logger()
    
    try:
        logger.debug("Checking paths and deck resolution", extra={
            "extra_fields": {
                "space_id": space_id,
                "deck_bank": deck_bank,
            }
        })
        
        if not deck_bank.startswith("GMLE::Bank::"):
            logger.error("Invalid deck_bank format", extra={
                "extra_fields": {"deck_bank": deck_bank}
            })
            raise ConfigError(
                f"invalid deck_bank format: {deck_bank}",
                code="INVALID_DECK_BANK_FORMAT",
                user_message=f"デッキバンクの形式が無効です: {deck_bank}",
            )
        
        expected_deck_suffix = f"GMLE::Bank::{space_id}"
        if deck_bank != expected_deck_suffix:
            logger.error("Deck bank mismatch", extra={
                "extra_fields": {
                    "deck_bank": deck_bank,
                    "expected": expected_deck_suffix,
                }
            })
            raise ConfigError(
                f"deck_bank mismatch: {deck_bank} != {expected_deck_suffix}",
                code="DECK_BANK_MISMATCH",
                user_message=f"デッキバンクが一致しません: {deck_bank} != {expected_deck_suffix}",
            )

        for key in ("data_root", "sources_root"):
            path = paths.get(key)
            if not isinstance(path, Path):
                logger.error("Path resolution failed", extra={
                    "extra_fields": {
                        "key": key,
                        "path_type": type(path).__name__,
                    }
                })
                raise ConfigError(
                    f"path resolution failed: {key}",
                    code="PATH_RESOLUTION_FAILED",
                    user_message=f"パスの解決に失敗しました: {key}",
                    details={"key": key, "path_type": type(path).__name__},
                )
        
        logger.debug("Paths and deck resolution check passed")
    except ConfigError:
        raise
    except Exception as exc:
        logger.error("Paths and deck resolution check failed", exc_info=True, extra={
            "extra_fields": {
                "space_id": space_id,
                "deck_bank": deck_bank,
            }
        })
        raise ConfigError(
            "paths and deck resolution check failed",
            code="PATHS_DECK_CHECK_FAILED",
            user_message="パスとデッキの解決の検証に失敗しました",
        ) from exc
