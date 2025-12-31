"""REST API response models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SpaceInfo(BaseModel):
    """Space information."""

    space_id: str = Field(..., description="Space ID")
    deck_bank: str = Field(..., description="Deck bank name")
    data_root: str = Field(..., description="Data root path")
    sources_root: str = Field(..., description="Sources root path")


class CreateSpaceRequest(BaseModel):
    """Create space request."""

    space_id: str = Field(..., description="Space ID (alphanumeric, hyphens, underscores only)", min_length=1, max_length=50)
    description: Optional[str] = Field(None, description="Optional description")


class AnkiStatusResponse(BaseModel):
    """Anki resources status response."""

    note_type_exists: bool = Field(..., description="Note type exists")
    deck_exists: bool = Field(..., description="Deck exists")
    note_type_name: str = Field(..., description="Note type name")
    deck_name: str = Field(..., description="Deck name")


class AnkiInitializeResponse(BaseModel):
    """Anki initialization response."""

    success: bool = Field(..., description="Initialization success")
    note_type_created: bool = Field(..., description="Note type was created")
    deck_created: bool = Field(..., description="Deck was created")
    message: str = Field(..., description="Result message")


class RunRequest(BaseModel):
    """Run request model."""

    mode: Optional[str] = Field(default="normal", description="Run mode (normal/batch)")


class RunResponse(BaseModel):
    """Run response model."""

    run_id: str = Field(..., description="Run ID")
    space_id: str = Field(..., description="Space ID")
    mode: str = Field(..., description="Run mode")
    status: str = Field(..., description="Run status (running/completed/failed)")
    today_count: Optional[int] = Field(None, description="Today count")
    new_accepted: Optional[int] = Field(None, description="New accepted count")
    degraded: bool = Field(default=False, description="Degraded mode")
    degraded_reason: Optional[str] = Field(None, description="Degraded reason")
    error_message: Optional[str] = Field(None, description="Error message")
    error_code: Optional[str] = Field(None, description="Error code (RATE_LIMIT, ANKI_ERROR, etc.)")
    error_phase: Optional[int] = Field(None, description="Phase number where error occurred")
    started_at: datetime = Field(..., description="Started at")
    completed_at: Optional[datetime] = Field(None, description="Completed at")


class ItemResponse(BaseModel):
    """Item response model."""

    id: str = Field(..., description="Item ID")
    source_id: str = Field(..., description="Source ID")
    domain_path: str = Field(..., description="Domain path")
    format: str = Field(..., description="Format (F/W/A)")
    depth: int = Field(..., description="Depth (1/2/3)")
    question: str = Field(..., description="Question")
    choices: List[str] = Field(..., description="Choices")
    answer: str = Field(..., description="Answer (A/B/C/D)")
    rationale: Dict[str, str] = Field(..., description="Rationale")
    source: Dict[str, Any] = Field(..., description="Source")
    meta: Dict[str, Any] = Field(..., description="Meta")
    retired: bool = Field(default=False, description="Retired")


class ConfigResponse(BaseModel):
    """Config response model."""

    space_id: str = Field(..., description="Space ID")
    params: Dict[str, Any] = Field(..., description="Parameters")
    paths: Dict[str, str] = Field(..., description="Paths")


class ConfigUpdateRequest(BaseModel):
    """Config update request model."""

    params: Optional[Dict[str, Any]] = Field(None, description="Parameters to update")


class LLMProviderInfo(BaseModel):
    """LLM Provider information."""

    api_url: str = Field(..., description="API URL")
    default_model: str = Field(..., description="Default model")
    available_models: List[str] = Field(..., description="Available models")
    api_key_configured: bool = Field(..., description="API key configured")


class LLMConfigResponse(BaseModel):
    """LLM configuration response."""

    active_provider: str = Field(..., description="Active LLM provider")
    providers: Dict[str, LLMProviderInfo] = Field(..., description="LLM providers")


class LLMConfigUpdateRequest(BaseModel):
    """LLM configuration update request."""

    active_provider: Optional[str] = Field(None, description="Active provider")
    provider_config: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="Provider configuration"
    )


class PromptInfo(BaseModel):
    """Prompt information."""

    description: str = Field(..., description="Prompt description")
    template: str = Field(..., description="Prompt template")


class PromptsConfigResponse(BaseModel):
    """Prompts configuration response."""

    stage1_extract: PromptInfo = Field(..., description="Stage 1 prompt")
    stage2_build_mcq: PromptInfo = Field(..., description="Stage 2 prompt")


class PromptsConfigUpdateRequest(BaseModel):
    """Prompts configuration update request."""

    stage1_extract: Optional[Dict[str, str]] = Field(None, description="Stage 1")
    stage2_build_mcq: Optional[Dict[str, str]] = Field(None, description="Stage 2")


class GlobalConfigResponse(BaseModel):
    """Global configuration response."""

    params: Dict[str, Any] = Field(..., description="Global default params")
    api: Dict[str, Any] = Field(..., description="API settings")
    logging: Dict[str, Any] = Field(..., description="Logging settings")
    http: Dict[str, Any] = Field(..., description="HTTP settings")
    rate_limit: Dict[str, Any] = Field(..., description="Rate limit settings")
    message: Optional[str] = Field(None, description="Optional message (e.g., restart required)")


class GlobalConfigUpdateRequest(BaseModel):
    """Global configuration update request."""

    params: Optional[Dict[str, Any]] = Field(None, description="Params to update")
    api: Optional[Dict[str, Any]] = Field(None, description="API settings")
    logging: Optional[Dict[str, Any]] = Field(None, description="Logging settings")
    http: Optional[Dict[str, Any]] = Field(None, description="HTTP settings")
    rate_limit: Optional[Dict[str, Any]] = Field(None, description="Rate limit settings")


class IngestResponse(BaseModel):
    """Ingest response model."""

    ingest_id: str = Field(..., description="Ingest ID")
    space_id: str = Field(..., description="Space ID")
    status: str = Field(..., description="Ingest status (completed/failed)")
    sources_count: int = Field(..., description="Total sources count")
    new_sources_count: int = Field(..., description="New sources count")
    filename: Optional[str] = Field(None, description="Uploaded filename")
    queue_path: str = Field(..., description="Queue file path")
    ingest_log_path: Optional[str] = Field(None, description="Ingest log path")
    started_at: datetime = Field(..., description="Started at")
    completed_at: Optional[datetime] = Field(None, description="Completed at")


class IngestHistoryItem(BaseModel):
    """Ingest history item."""

    ingest_id: str = Field(..., description="Ingest ID")
    source: str = Field(..., description="Source type (textfile/readwise/upload)")
    sources_count: int = Field(..., description="Sources count")
    new_sources_count: int = Field(..., description="New sources count")
    filename: Optional[str] = Field(None, description="Filename")
    started_at: datetime = Field(..., description="Started at")


class IngestHistoryResponse(BaseModel):
    """Ingest history response."""

    ingests: List[IngestHistoryItem] = Field(..., description="Ingest history")


class UploadResponse(BaseModel):
    """File upload response."""

    filename: str = Field(..., description="Uploaded filename")
    file_path: str = Field(..., description="Saved file path")
    size: int = Field(..., description="File size in bytes")
    uploaded_at: datetime = Field(..., description="Upload timestamp")


class IngestRequest(BaseModel):
    """Ingest request model."""

    file_path: str = Field(..., description="File path to ingest")
    title: Optional[str] = Field(None, description="Optional title for the source")


class UploadedFileInfo(BaseModel):
    """Uploaded file information."""

    filename: str = Field(..., description="Filename")
    file_path: str = Field(..., description="Relative file path from sources_root")
    size: int = Field(..., description="File size in bytes")
    modified_at: datetime = Field(..., description="File modification time")


class UploadedFilesResponse(BaseModel):
    """Uploaded files list response."""

    files: List[UploadedFileInfo] = Field(..., description="List of uploaded files")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error detail")
    code: Optional[str] = Field(None, description="Error code")


class ServiceStatus(BaseModel):
    """Service status model."""

    name: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status (running/stopped/warning/error)")
    pid: Optional[int] = Field(None, description="Process ID")
    port: Optional[int] = Field(None, description="Port number")
    health_check: Optional[str] = Field(None, description="Health check URL")
    warning: Optional[str] = Field(None, description="Warning message")
    error: Optional[str] = Field(None, description="Error message")
    message: Optional[str] = Field(None, description="Info message")


class SystemStatusResponse(BaseModel):
    """System status response."""

    services: Dict[str, ServiceStatus] = Field(..., description="Services status")


class ApiKeyStatusResponse(BaseModel):
    """API key status response."""

    valid: bool = Field(..., description="API key is valid")
    error: Optional[str] = Field(None, description="Error message if invalid")
    key_type: Optional[str] = Field(None, description="Key type (trial/production)")
    has_quota: bool = Field(..., description="Has available quota")
    error_detail: Optional[str] = Field(None, description="Detailed error information")


class PrerequisitesCheckResponse(BaseModel):
    """Prerequisites check response."""

    all_passed: bool = Field(..., description="All prerequisites passed")
    checks: Dict[str, Dict[str, Any]] = Field(..., description="Individual check results")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    errors: List[str] = Field(default_factory=list, description="Error messages")

