"""Ingest executor (background task)."""

from __future__ import annotations

from typing import Any, Dict

from gmle.app.api.internal.ingest_api import get_ingest_api
from gmle.app.ingest.writer import write_ingest_log, write_queue
from gmle.app.infra.time_id import today_str


def execute_ingest(
    context: Dict[str, Any],
    ingest_id: str,
    file_content: bytes,
    filename: str,
    title: str | None,
) -> None:
    """Execute ingest in background from file content."""
    try:
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
        
    except Exception as e:
        # Log error (could be enhanced with proper logging)
        print(f"Ingest error: {e}")


def execute_ingest_from_file(
    context: Dict[str, Any],
    ingest_id: str,
    file_path: str,
    title: str | None,
) -> None:
    """Execute ingest in background from existing file."""
    try:
        # Get ingest API instance
        ingest_api = get_ingest_api(config=context)
        
        # Ingest from file path
        sources = ingest_api.ingest_textfile(file_path, title=title)
        
        # Write to queue
        paths = context["paths"]
        date_str = today_str()
        new_sources = write_queue(paths["queue"], sources)
        
        # Write ingest log
        from pathlib import Path
        filename = Path(file_path).name
        write_ingest_log(paths["ingest_log_dir"], date_str, {
            "date": date_str,
            "source": "textfile",
            "sources_count": len(sources),
            "new_sources_count": len(new_sources),
            "filename": filename,
        })
        
    except Exception as e:
        # Log error (could be enhanced with proper logging)
        print(f"Ingest error: {e}")

