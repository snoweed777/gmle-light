"""AnkiConnect connectivity check."""

from __future__ import annotations

from gmle.app.adapters.anki_client import invoke
from gmle.app.infra.errors import AnkiError
from gmle.app.infra.logger import get_logger, log_exception


def check_anki_connect() -> None:
    """Check AnkiConnect connectivity (version)."""
    logger = get_logger()
    
    try:
        logger.debug("Checking AnkiConnect connectivity")
        version = invoke("version")
        if not isinstance(version, int):
            logger.error("AnkiConnect version check failed", extra={
                "extra_fields": {
                    "version_type": type(version).__name__,
                    "version_value": str(version),
                }
            })
            raise AnkiError(
                f"version returned non-int: {type(version)}",
                code="ANKI_VERSION_INVALID",
                user_message="AnkiConnectのバージョン情報が無効です",
            )
        logger.debug("AnkiConnect connectivity check passed", extra={
            "extra_fields": {"version": version}
        })
    except AnkiError:
        raise
    except Exception as exc:
        log_exception(logger, "AnkiConnect connectivity check failed", exc)
        raise AnkiError(
            "anki connect unavailable",
            code="ANKI_CONNECT_UNAVAILABLE",
            user_message="AnkiConnectに接続できません。Ankiが起動しているか確認してください。",
        ) from exc
