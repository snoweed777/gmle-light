"""Items.json parse check."""

from __future__ import annotations

from pathlib import Path

from gmle.app.infra.errors import SOTError
from gmle.app.infra.logger import get_logger, log_exception
from gmle.app.sot.items_io import read_items


def check_items_parse(items_path: Path) -> None:
    """Check items.json parse capability."""
    logger = get_logger()
    
    if not items_path.exists():
        logger.debug("items.json does not exist, skipping parse check")
        return
    
    try:
        logger.debug("Checking items.json parse capability", extra={
            "extra_fields": {"items_path": str(items_path)}
        })
        items = read_items(items_path)
        logger.debug("items.json parse check passed", extra={
            "extra_fields": {"item_count": len(items)}
        })
    except SOTError:
        raise
    except Exception as exc:
        log_exception(
            logger,
            "items.json parse check failed",
            exc,
            items_path=str(items_path),
        )
        raise SOTError(
            f"items.json parse failed: {items_path}",
            code="ITEMS_PARSE_FAILED",
            user_message=f"items.jsonの解析に失敗しました: {items_path}",
        ) from exc
