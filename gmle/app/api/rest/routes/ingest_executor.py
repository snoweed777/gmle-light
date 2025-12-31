"""Ingest executor (background task)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from gmle.app.api.internal.ingest_api import get_ingest_api
from gmle.app.ingest.writer import write_ingest_log, write_queue
from gmle.app.infra.logger import get_logger, log_exception
from gmle.app.infra.time_id import today_str


def execute_ingest(
    context: Dict[str, Any],
    ingest_id: str,
    file_content: bytes,
    filename: str,
    title: str | None,
) -> None:
    """Execute ingest in background from file content."""
    space_id = context.get("space")
    logger = get_logger(space_id=space_id)
    
    try:
        logger.info("Starting ingest from uploaded file", extra={
            "extra_fields": {
                "ingest_id": ingest_id,
                "filename": filename,
                "title": title,
            }
        })
        
        # Get ingest API instance
        ingest_api = get_ingest_api(config=context)
        
        # Ingest from uploaded file
        sources = ingest_api.ingest_uploaded_file(
            file_content=file_content,
            filename=filename,
            title=title,
        )
        
        # Write to queue
        paths = context["paths"]
        date_str = today_str()
        new_sources = write_queue(paths["queue"], sources)
        
        # Write ingest log
        write_ingest_log(paths["ingest_log_dir"], date_str, {
            "date": date_str,
            "source": "upload",
            "sources_count": len(sources),
            "new_sources_count": len(new_sources),
            "filename": filename,
        })
        
        logger.info("Ingest completed successfully", extra={
            "extra_fields": {
                "ingest_id": ingest_id,
                "sources_count": len(sources),
                "new_sources_count": len(new_sources),
            }
        })
        
    except Exception as e:
        log_exception(
            logger,
            "Ingest failed",
            e,
            ingest_id=ingest_id,
            filename=filename,
        )


def execute_ingest_from_file(
    context: Dict[str, Any],
    ingest_id: str,
    file_path: str,
    title: str | None,
) -> None:
    """Execute ingest in background from existing file."""
    space_id = context.get("space")
    logger = get_logger(space_id=space_id)
    
    try:
        logger.info("Starting ingest from file", extra={
            "extra_fields": {
                "ingest_id": ingest_id,
                "file_path": file_path,
                "title": title,
            }
        })
        
        # Get ingest API instance
        ingest_api = get_ingest_api(config=context)
        
        # Ingest from file path
        sources = ingest_api.ingest_textfile(file_path, title=title)
        
        # Write to queue
        paths = context["paths"]
        date_str = today_str()
        new_sources = write_queue(paths["queue"], sources)
        
        # Write ingest log
        filename = Path(file_path).name
        write_ingest_log(paths["ingest_log_dir"], date_str, {
            "date": date_str,
            "source": "textfile",
            "sources_count": len(sources),
            "new_sources_count": len(new_sources),
            "filename": filename,
        })
        
        logger.info("Ingest completed successfully", extra={
            "extra_fields": {
                "ingest_id": ingest_id,
                "sources_count": len(sources),
                "new_sources_count": len(new_sources),
            }
        })
        
    except Exception as e:
        log_exception(
            logger,
            "Ingest failed",
            e,
            ingest_id=ingest_id,
            file_path=file_path,
        )

