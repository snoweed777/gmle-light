"""Phase 8: Commit and Sync."""

from __future__ import annotations

from typing import Any, Dict

from gmle.app.adapters.anki_client import sync as anki_sync
from gmle.app.infra.logger import get_logger, log_exception, with_fields
from gmle.app.infra.runlog import write_runlog
from gmle.app.infra.time_id import datestamp_and_run_id
from gmle.app.sot.items_io import write_items
from gmle.app.sot.ledger_io import append_ledger


def execute(context: Dict[str, Any]) -> None:
    """Commit items/ledger/runlog and sync Anki (Phase 8)."""
    logger = get_logger(space_id=context.get("space_id"))
    paths = context["paths"]
    items = context["items"]
    new_source_ids = context.get("new_source_ids", [])

    logger.info("Committing data", **with_fields(logger,
        items_count=len(items),
        new_source_ids_count=len(new_source_ids),
        run_id=context.get("run_id"),
    ))

    write_items(paths["items"], items)
    logger.debug("Items written to SOT", **with_fields(logger, path=str(paths["items"])))
    
    for source_id in new_source_ids:
        date_str, run_id = datestamp_and_run_id()
        append_ledger(paths["ledger"], {
            "source_id": source_id,
            "used_at": date_str,
            "run_id": run_id,
        })
    logger.debug("Ledger updated", **with_fields(logger, new_entries=len(new_source_ids)))

    runlog_payload = {
        "run_id": context.get("run_id", ""),
        "space_id": context["space_id"],
        "mode": context.get("mode", "normal"),
        "degraded": context.get("degraded", False),
        "degraded_reason": context.get("degraded_reason", ""),
        "today_count": len(context.get("today_note_ids", [])),
        "new_generated": context.get("new_generated", 0),
        "new_accepted": len(new_source_ids),
        "maintain_count": context.get("maintain_count", 0),
    }
    runlog_path = write_runlog(paths["runlog_dir"], context.get("run_id", ""), runlog_payload)
    logger.info("Runlog written", **with_fields(logger, runlog_path=str(runlog_path), **runlog_payload))

    # Auto-sync Anki with AnkiWeb (skip in batch mode)
    if context.get("mode") != "batch":
        try:
            logger.debug("Syncing Anki with AnkiWeb")
            anki_sync(config=context)
            logger.info("AnkiWeb sync completed successfully")
        except Exception as exc:
            log_exception(logger, "AnkiWeb sync failed (non-critical)", exc, run_id=context.get("run_id"))
