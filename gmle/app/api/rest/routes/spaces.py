"""Space-related endpoints."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

import yaml
from fastapi import APIRouter, HTTPException, status

from gmle.app.adapters.anki_client import (
    create_deck,
    create_model,
    deck_names,
    model_names,
)
from gmle.app.api.rest.errors import raise_not_found
from gmle.app.api.rest.models import (
    AnkiInitializeResponse,
    AnkiStatusResponse,
    CreateSpaceRequest,
    SpaceInfo,
)
from gmle.app.config.env_paths import get_spaces_config_dir
from gmle.app.config.loader import load_config
from gmle.app.config.merger import defaults
from gmle.app.infra.errors import AnkiError
from gmle.app.infra.logger import get_logger, log_exception

router = APIRouter(prefix="/spaces", tags=["spaces"])

NOTE_TYPE_NAME = "GMLE_MCQA"

logger = get_logger("gmle.api.rest.spaces")


@router.get("", response_model=List[SpaceInfo])
async def list_spaces() -> List[SpaceInfo]:
    """List available spaces."""
    # Use environment-aware path resolution
    spaces_dir = get_spaces_config_dir()
    
    if not spaces_dir.exists():
        logger.warning(f"Spaces directory not found: {spaces_dir}")
        return []

    spaces: List[SpaceInfo] = []
    errors: List[str] = []
    
    for yaml_file in spaces_dir.glob("*.yaml"):
        space_id = yaml_file.stem
        # Skip backup files
        if "." in space_id and space_id.split(".")[-1].isdigit():
            continue
        try:
            config = load_config({"space": space_id})
            spaces.append(SpaceInfo(
                space_id=space_id,
                deck_bank=config["deck_bank"],
                data_root=str(config["paths"]["data_root"]),
                sources_root=str(config["paths"]["sources_root"]),
            ))
        except Exception as e:
            error_msg = f"Failed to load space '{space_id}': {e}"
            log_exception(logger, error_msg, e, space_id=space_id, yaml_file=str(yaml_file))
            errors.append(error_msg)
            continue

    if errors:
        logger.warning(
            f"Failed to load {len(errors)} space(s) out of {len(list(spaces_dir.glob('*.yaml')))} total",
            extra={"extra_fields": {"error_count": len(errors), "errors": errors}}
        )
    
    logger.debug(f"Loaded {len(spaces)} space(s) successfully")
    return spaces


@router.post("", response_model=SpaceInfo, status_code=201)
async def create_space(request: CreateSpaceRequest) -> SpaceInfo:
    """Create a new space."""
    space_id = request.space_id
    
    # Validate space_id format (alphanumeric, hyphens, underscores only)
    if not re.match(r'^[a-zA-Z0-9_-]+$', space_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Space ID must contain only alphanumeric characters, hyphens, and underscores",
        )
    
    # Check if space already exists
    spaces_dir = get_spaces_config_dir()
    space_config_path = spaces_dir / f"{space_id}.yaml"
    
    if space_config_path.exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Space '{space_id}' already exists",
        )
    
    try:
        # Create spaces directory if it doesn't exist
        spaces_dir.mkdir(parents=True, exist_ok=True)
        
        # Get default params from merger
        default_config = defaults()
        
        # Create space configuration
        space_config = {
            "space_id": space_id,
            "deck_bank": f"GMLE::Bank::{space_id}",
            "data_root": f"data/{space_id}",
            "sources_root": f"sources/{space_id}",
            "params": default_config["params"],
        }
        
        # Write YAML file
        with open(space_config_path, 'w', encoding='utf-8') as f:
            yaml.dump(space_config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        logger.info(f"Created space configuration: {space_config_path}")
        
        # Create data and sources directories
        # Get the base paths (assuming they're relative to /app in Docker)
        from gmle.app.config.env_paths import get_data_dir, get_sources_dir
        
        data_dir = get_data_dir() / space_id
        sources_dir = get_sources_dir() / space_id
        
        data_dir.mkdir(parents=True, exist_ok=True)
        sources_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created directories: {data_dir}, {sources_dir}")
        
        # Return created space info
        return SpaceInfo(
            space_id=space_id,
            deck_bank=space_config["deck_bank"],
            data_root=str(space_config["data_root"]),
            sources_root=str(space_config["sources_root"]),
        )
    
    except Exception as e:
        # Cleanup on failure
        if space_config_path.exists():
            space_config_path.unlink()
        log_exception(logger, f"Failed to create space '{space_id}'", e, space_id=space_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create space: {str(e)}",
        )


@router.get("/{space_id}", response_model=SpaceInfo)
async def get_space(space_id: str) -> SpaceInfo:
    """Get space information."""
    try:
        config = load_config({"space": space_id})
        return SpaceInfo(
            space_id=space_id,
            deck_bank=config["deck_bank"],
            data_root=str(config["paths"]["data_root"]),
            sources_root=str(config["paths"]["sources_root"]),
        )
    except Exception as e:
        log_exception(logger, f"Failed to load space '{space_id}'", e, space_id=space_id)
        raise_not_found("Space", space_id)
        return SpaceInfo(space_id="", deck_bank="", data_root="", sources_root="")  # Never reached


@router.get("/{space_id}/anki/status", response_model=AnkiStatusResponse)
async def get_anki_status(space_id: str) -> AnkiStatusResponse:
    """Get Anki resources status for a space."""
    # Validate space exists
    try:
        config = load_config({"space": space_id})
    except Exception as e:
        log_exception(logger, f"Failed to load space '{space_id}' for Anki status check", e, space_id=space_id)
        raise_not_found("Space", space_id)

    # Get deck bank name
    deck_bank = config.get("deck_bank") or f"GMLE::Bank::{space_id}"

    try:
        # Check Note Type existence
        existing_models = model_names()
        note_type_exists = NOTE_TYPE_NAME in existing_models

        # Check Deck existence
        existing_decks = deck_names()
        deck_exists = deck_bank in existing_decks

        return AnkiStatusResponse(
            note_type_exists=note_type_exists,
            deck_exists=deck_exists,
            note_type_name=NOTE_TYPE_NAME,
            deck_name=deck_bank,
        )
    except AnkiError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to check Anki status: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.post("/{space_id}/anki/initialize", response_model=AnkiInitializeResponse)
async def initialize_space(space_id: str) -> AnkiInitializeResponse:
    """Initialize Anki resources for a space (create Note Type and Deck if needed)."""
    # Validate space exists
    try:
        config = load_config({"space": space_id})
    except Exception as e:
        log_exception(logger, f"Failed to load space '{space_id}' for initialization", e, space_id=space_id)
        raise_not_found("Space", space_id)

    # Get deck bank name
    deck_bank = config.get("deck_bank") or f"GMLE::Bank::{space_id}"

    note_type_created = False
    deck_created = False
    messages = []

    try:
        # Check and create Note Type
        existing_models = model_names()
        if NOTE_TYPE_NAME not in existing_models:
            try:
                create_model(NOTE_TYPE_NAME)
                note_type_created = True
                messages.append(f"Created Note Type: {NOTE_TYPE_NAME}")
            except AnkiError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Failed to create Note Type: {str(e)}",
                )
        else:
            messages.append(f"Note Type already exists: {NOTE_TYPE_NAME}")

        # Check and create Deck
        existing_decks = deck_names()
        if deck_bank not in existing_decks:
            try:
                create_deck(deck_bank)
                deck_created = True
                messages.append(f"Created Deck: {deck_bank}")
            except AnkiError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Failed to create Deck: {str(e)}",
                )
        else:
            messages.append(f"Deck already exists: {deck_bank}")

        success = True
        if note_type_created or deck_created:
            message = " ".join(messages)
        else:
            message = "すべてのリソースが既に存在しています"

        return AnkiInitializeResponse(
            success=success,
            note_type_created=note_type_created,
            deck_created=deck_created,
            message=message,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )

