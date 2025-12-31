"""Ingest-related endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, File, UploadFile

from gmle.app.api.rest.errors import raise_not_found
from gmle.app.api.rest.models import (
    IngestRequest,
    IngestResponse,
    IngestHistoryItem,
    IngestHistoryResponse,
    UploadResponse,
    UploadedFileInfo,
    UploadedFilesResponse,
)
from gmle.app.config.loader import load_config
from gmle.app.infra.jsonio import read_json
from gmle.app.infra.time_id import today_str
from .ingest_executor import execute_ingest_from_file

router = APIRouter(prefix="/spaces/{space_id}/ingest", tags=["ingest"])


@router.get("/files", response_model=UploadedFilesResponse)
async def list_uploaded_files(space_id: str) -> UploadedFilesResponse:
    """List uploaded files."""
    # Validate space exists
    try:
        context = load_config({"space": space_id})
    except Exception:
        raise_not_found("Space", space_id)
    
    # Get texts directory
    texts_dir = context["paths"]["sources_root"] / "texts"
    texts_dir.mkdir(parents=True, exist_ok=True)
    
    # List files
    files = []
    for file_path in sorted(texts_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if file_path.is_file():
            stat = file_path.stat()
            files.append(
                UploadedFileInfo(
                    filename=file_path.name,
                    file_path=str(file_path.relative_to(context["paths"]["sources_root"])),
                    size=stat.st_size,
                    modified_at=datetime.fromtimestamp(stat.st_mtime),
                )
            )
    
    return UploadedFilesResponse(files=files)


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    space_id: str,
    file: UploadFile = File(...),
) -> UploadResponse:
    """Upload file (save only, no ingest)."""
    # Validate space exists
    try:
        context = load_config({"space": space_id})
    except Exception:
        raise_not_found("Space", space_id)
    
    # Validate file type
    filename = file.filename or "unknown"
    suffix = filename.lower().split(".")[-1] if "." in filename else ""
    if suffix not in ("txt", "docx"):
        raise ValueError(f"Unsupported file type: {suffix}. Supported: .txt, .docx")
    
    # Read file content
    file_content = await file.read()
    
    # Save to texts directory
    texts_dir = context["paths"]["sources_root"] / "texts"
    texts_dir.mkdir(parents=True, exist_ok=True)
    file_path = texts_dir / filename
    
    # Write file
    file_path.write_bytes(file_content)
    
    return UploadResponse(
        filename=filename,
        file_path=str(file_path.relative_to(context["paths"]["sources_root"])),
        size=len(file_content),
        uploaded_at=datetime.now(),
    )


@router.post("", response_model=IngestResponse, status_code=202)
async def ingest_file(
    space_id: str,
    request: IngestRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> IngestResponse:
    """Ingest from uploaded file."""
    # Validate space exists
    try:
        context = load_config({"space": space_id})
    except Exception:
        raise_not_found("Space", space_id)
    
    # Validate file path
    file_path = context["paths"]["sources_root"] / request.file_path
    if not file_path.exists():
        raise ValueError(f"File not found: {request.file_path}")
    
    # Generate ingest ID
    date_str = today_str()
    ingest_id = f"{date_str}_{file_path.name}"
    
    # Execute ingest in background
    background_tasks.add_task(
        execute_ingest_from_file,
        context,
        ingest_id,
        str(file_path),
        request.title,
    )
    
    return IngestResponse(
        ingest_id=ingest_id,
        space_id=space_id,
        status="processing",
        sources_count=0,
        new_sources_count=0,
        filename=file_path.name,
        queue_path=str(context["paths"]["queue"]),
        ingest_log_path=None,
        started_at=datetime.now(),
        completed_at=None,
    )


@router.get("/status/{ingest_id}", response_model=IngestResponse)
async def get_ingest_status(space_id: str, ingest_id: str) -> IngestResponse:
    """Get ingest status by ingest ID."""
    # Validate space exists
    try:
        context = load_config({"space": space_id})
    except Exception:
        raise_not_found("Space", space_id)
    
    # Parse ingest ID (format: date_filename)
    # Note: filename may contain underscores, so we split only on first underscore
    if "_" not in ingest_id:
        raise ValueError(f"Invalid ingest ID format: {ingest_id}")
    
    parts = ingest_id.split("_", 1)
    date_str = parts[0]
    
    # Read ingest log
    log_path = context["paths"]["ingest_log_dir"] / f"{date_str}.json"
    if not log_path.exists():
        # Ingest may still be processing
        return IngestResponse(
            ingest_id=ingest_id,
            space_id=space_id,
            status="processing",
            sources_count=0,
            new_sources_count=0,
            filename=None,
            queue_path=str(context["paths"]["queue"]),
            ingest_log_path=None,
            started_at=datetime.fromisoformat(date_str),
            completed_at=None,
        )
    
    log_data = read_json(log_path)
    
    # Find matching entry (if log contains multiple entries)
    # For now, assume one entry per date
    sources_count = log_data.get("sources_count", 0)
    new_sources_count = log_data.get("new_sources_count", 0)
    
    # Check if completed (log exists means completed)
    status = "completed"
    completed_at = datetime.fromtimestamp(log_path.stat().st_mtime)
    
    return IngestResponse(
        ingest_id=ingest_id,
        space_id=space_id,
        status=status,
        sources_count=sources_count,
        new_sources_count=new_sources_count,
        filename=log_data.get("filename"),
        queue_path=str(context["paths"]["queue"]),
        ingest_log_path=str(log_path.relative_to(context["paths"]["sources_root"])),
        started_at=datetime.fromisoformat(date_str),
        completed_at=completed_at,
    )


@router.get("/history", response_model=IngestHistoryResponse)
async def get_ingest_history(space_id: str) -> IngestHistoryResponse:
    """Get ingest history."""
    # Validate space exists
    try:
        context = load_config({"space": space_id})
    except Exception:
        raise_not_found("Space", space_id)
    
    # Read all ingest logs
    log_dir = context["paths"]["ingest_log_dir"]
    log_dir.mkdir(parents=True, exist_ok=True)
    
    ingests = []
    for log_path in sorted(log_dir.glob("*.json"), reverse=True):
        try:
            log_data = read_json(log_path)
            date_str = log_path.stem
            
            # Create ingest ID from date and filename
            filename = log_data.get("filename", "unknown")
            ingest_id = f"{date_str}_{filename}"
            
            # Use file modification time as started_at (actual ingest time)
            started_at = datetime.fromtimestamp(log_path.stat().st_mtime)
            
            ingests.append(
                IngestHistoryItem(
                    ingest_id=ingest_id,
                    source=log_data.get("source", "unknown"),
                    sources_count=log_data.get("sources_count", 0),
                    new_sources_count=log_data.get("new_sources_count", 0),
                    filename=filename,
                    started_at=started_at,
                )
            )
        except Exception:
            # Skip invalid log files
            continue
    
    return IngestHistoryResponse(ingests=ingests)

