"""Run-related endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from gmle.app.adapters.anki_client import deck_names, model_names
from gmle.app.api.rest.errors import raise_not_found
from gmle.app.api.rest.models import PrerequisitesCheckResponse, RunRequest, RunResponse
from gmle.app.config.loader import load_config
from gmle.app.http.cohere_client import check_api_key_status
from gmle.app.infra.errors import AnkiError
from gmle.app.infra.time_id import datestamp_and_run_id
from gmle.app.sot.queue_io import read_queue
from .runs_executor import execute_run
from .runs_status import get_run_status

router = APIRouter(prefix="/spaces/{space_id}/runs", tags=["runs"])

# In-memory run status store (for async execution)
_run_status: Dict[str, Dict[str, Any]] = {}


def _check_prerequisites(space_id: str) -> PrerequisitesCheckResponse:
    """Check prerequisites before run execution."""
    checks: Dict[str, Dict[str, Any]] = {}
    warnings: list[str] = []
    errors: list[str] = []
    
    # Check API key status (for active LLM provider)
    try:
        from gmle.app.config.getter import get_llm_config
        llm_config = get_llm_config()
        active_provider = llm_config.get("active_provider", "cohere")
        
        if active_provider == "cohere":
            api_status = check_api_key_status()
        elif active_provider == "gemini":
            from gmle.app.http.gemini_client import check_api_key_status as gemini_check
            api_status = gemini_check()
        elif active_provider == "groq":
            from gmle.app.http.groq_client import check_api_key_status as groq_check
            api_status = groq_check()
        else:
            api_status = {
                "valid": False,
                "error": f"Unknown provider: {active_provider}",
                "key_type": None,
                "has_quota": False,
            }
        
        checks["api_key"] = api_status
        checks["api_key"]["provider"] = active_provider
        
        if not api_status["valid"]:
            errors.append(f"API key is invalid: {api_status.get('error', 'Unknown error')}")
        elif not api_status["has_quota"]:
            error_msg = api_status.get('error', 'Quota limit reached')
            if active_provider == "gemini" and "daily" in error_msg.lower():
                errors.append(f"API key has no quota: {error_msg} (Daily limit reached)")
            else:
                errors.append(f"API key has no quota: {error_msg}")
        elif api_status.get("key_type") == "trial":
            warnings.append("Using Trial API key (limited to 1000 calls/month)")
        elif api_status.get("key_type") == "free" and active_provider == "gemini":
            warnings.append("Using Google AI Studio free tier (1500 requests/day)")
    except Exception as e:
        checks["api_key"] = {"valid": False, "error": str(e)}
        errors.append(f"Failed to check API key: {e}")
    
    # Check space config
    try:
        config = load_config({"space": space_id})
        checks["space_config"] = {"valid": True}
        
        # Check queue has sources
        queue_path = config["paths"]["queue"]
        sources = read_queue(queue_path)
        checks["queue_sources"] = {
            "valid": len(sources) > 0,
            "count": len(sources),
        }
        if len(sources) == 0:
            errors.append("No sources available in queue.jsonl")
        
        # Check Anki resources
        try:
            deck_bank = config.get("deck_bank") or f"GMLE::Bank::{space_id}"
            existing_decks = deck_names()
            existing_models = model_names()
            
            checks["anki_resources"] = {
                "deck_exists": deck_bank in existing_decks,
                "note_type_exists": "GMLE_MCQA" in existing_models,
            }
            
            if deck_bank not in existing_decks:
                warnings.append(f"Deck '{deck_bank}' does not exist (will be created)")
            if "GMLE_MCQA" not in existing_models:
                warnings.append("Note Type 'GMLE_MCQA' does not exist (will be created)")
        except AnkiError as e:
            checks["anki_resources"] = {"valid": False, "error": str(e)}
            errors.append(f"Anki connection failed: {e}")
        except Exception as e:
            checks["anki_resources"] = {"valid": False, "error": str(e)}
            warnings.append(f"Could not check Anki resources: {e}")
            
    except Exception as e:
        checks["space_config"] = {"valid": False, "error": str(e)}
        errors.append(f"Failed to load space config: {e}")
    
    all_passed = len(errors) == 0
    return PrerequisitesCheckResponse(
        all_passed=all_passed,
        checks=checks,
        warnings=warnings,
        errors=errors,
    )


@router.post("", response_model=RunResponse, status_code=202)
async def create_run(
    space_id: str,
    request: RunRequest,
    background_tasks: BackgroundTasks,
) -> RunResponse:
    """Create and execute a new run."""
    # Validate space exists
    try:
        load_config({"space": space_id})
    except Exception:
        raise_not_found("Space", space_id)
    
    # Check prerequisites
    import asyncio
    prereq = await asyncio.to_thread(_check_prerequisites, space_id)
    
    # Block execution if critical errors exist
    if not prereq.all_passed:
        error_msg = "; ".join(prereq.errors)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Prerequisites check failed: {error_msg}",
        )

    # Generate run ID
    _, run_id = datestamp_and_run_id()
    mode = request.mode or "normal"

    # Initialize run status
    _run_status[run_id] = {
        "run_id": run_id,
        "space_id": space_id,
        "mode": mode,
        "status": "running",
        "started_at": datetime.now().isoformat(),
    }

    # Execute in background
    background_tasks.add_task(
        execute_run, space_id, run_id, mode, _run_status
    )

    return RunResponse(
        run_id=run_id,
        space_id=space_id,
        mode=mode,
        status="running",
        today_count=None,
        new_accepted=None,
        degraded=False,
        degraded_reason=None,
        error_message=None,
        error_code=None,
        error_phase=None,
        started_at=datetime.now(),
        completed_at=None,
    )


@router.get("/prerequisites", response_model=PrerequisitesCheckResponse)
async def check_prerequisites(space_id: str) -> PrerequisitesCheckResponse:
    """Check prerequisites before run execution."""
    try:
        load_config({"space": space_id})
    except Exception:
        raise_not_found("Space", space_id)
    
    import asyncio
    return await asyncio.to_thread(_check_prerequisites, space_id)


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(space_id: str, run_id: str) -> RunResponse:
    """Get run status."""
    return get_run_status(space_id, run_id, _run_status)


@router.get("", response_model=list[RunResponse])
async def list_runs(space_id: str) -> list[RunResponse]:
    """List all runs for a space."""
    from pathlib import Path
    import json
    
    # Validate space exists
    try:
        config = load_config({"space": space_id})
    except Exception:
        raise_not_found("Space", space_id)
    
    # Get runlog directory
    runlog_dir = Path(config["paths"].get("runlog_dir", config["paths"]["data_root"] / "runs"))
    
    runs = []
    
    # Check in-memory runs first
    for run_id, status_data in _run_status.items():
        if status_data.get("space_id") == space_id:
            runs.append(get_run_status(space_id, run_id, _run_status))
    
    # Get runs from runlog files
    if runlog_dir.exists():
        # Iterate through date directories (e.g., 2025-12-31)
        for date_dir in sorted(runlog_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
            
            # Iterate through run files in each date directory
            for run_file in sorted(date_dir.glob("*.json"), reverse=True):
                try:
                    with run_file.open() as f:
                        data = json.load(f)
                    
                    run_id = data.get("run_id", run_file.stem)
                    
                    # Skip if already in memory
                    if run_id in _run_status:
                        continue
                    
                    # Skip if not for this space
                    if data.get("space_id") != space_id:
                        continue
                    
                    runs.append(RunResponse(
                        run_id=run_id,
                        space_id=space_id,
                        mode=data.get("mode", "normal"),
                        status=data.get("status", "completed"),
                        today_count=data.get("today_count"),
                        new_accepted=data.get("new_accepted"),
                        degraded=data.get("degraded", False),
                        degraded_reason=data.get("degraded_reason"),
                        error_message=data.get("error_message"),
                        error_code=data.get("error_code"),
                        error_phase=data.get("error_phase"),
                        started_at=datetime.fromisoformat(
                            data.get("started_at", datetime.now().isoformat())
                        ),
                        completed_at=(
                            datetime.fromisoformat(data.get("completed_at"))
                            if data.get("completed_at")
                            else None
                        ),
                    ))
                except Exception:
                    # Skip invalid files
                    continue
    
    return runs

