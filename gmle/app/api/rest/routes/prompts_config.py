"""Prompts configuration endpoints."""

from __future__ import annotations

import shutil
from datetime import datetime
from typing import Any, Dict

import yaml
from fastapi import APIRouter, HTTPException

from gmle.app.api.rest.models import (
    PromptInfo,
    PromptsConfigResponse,
    PromptsConfigUpdateRequest,
)
from gmle.app.config.env_paths import get_config_dir

router = APIRouter(prefix="/config/prompts", tags=["prompts_config"])


def _load_global_config() -> Dict[str, Any]:
    """Load global config from gmle.yaml."""
    config_file = get_config_dir() / "gmle.yaml"
    
    if not config_file.exists():
        raise HTTPException(status_code=404, detail="Global config not found")

    with open(config_file, encoding="utf-8") as f:
        result: Dict[str, Any] = yaml.safe_load(f) or {}
        return result


def _save_global_config(config: Dict[str, Any]) -> None:
    """Save global config to gmle.yaml with backup."""
    config_file = get_config_dir() / "gmle.yaml"

    # Create backup if file exists
    if config_file.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = config_file.with_suffix(f".{timestamp}.backup")
        shutil.copy2(config_file, backup_file)

    # Save updated config
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


@router.get("", response_model=PromptsConfigResponse)
async def get_prompts_config() -> PromptsConfigResponse:
    """Get prompts configuration."""
    config = _load_global_config()
    prompts_config = config.get("prompts", {})

    stage1 = prompts_config.get("stage1_extract", {})
    stage2 = prompts_config.get("stage2_build_mcq", {})

    return PromptsConfigResponse(
        stage1_extract=PromptInfo(
            description=stage1.get("description", "Stage 1: 事実抽出プロンプト"),
            template=stage1.get("template", ""),
        ),
        stage2_build_mcq=PromptInfo(
            description=stage2.get("description", "Stage 2: MCQ生成プロンプト"),
            template=stage2.get("template", ""),
        ),
    )


@router.put("", response_model=PromptsConfigResponse)
async def update_prompts_config(
    request: PromptsConfigUpdateRequest,
) -> PromptsConfigResponse:
    """Update prompts configuration."""
    config = _load_global_config()

    if "prompts" not in config:
        config["prompts"] = {}

    # Update stage1_extract
    if request.stage1_extract:
        if "stage1_extract" not in config["prompts"]:
            config["prompts"]["stage1_extract"] = {}

        if "template" in request.stage1_extract:
            config["prompts"]["stage1_extract"]["template"] = request.stage1_extract[
                "template"
            ]
        if "description" in request.stage1_extract:
            config["prompts"]["stage1_extract"]["description"] = (
                request.stage1_extract["description"]
            )

    # Update stage2_build_mcq
    if request.stage2_build_mcq:
        if "stage2_build_mcq" not in config["prompts"]:
            config["prompts"]["stage2_build_mcq"] = {}

        if "template" in request.stage2_build_mcq:
            config["prompts"]["stage2_build_mcq"]["template"] = (
                request.stage2_build_mcq["template"]
            )
        if "description" in request.stage2_build_mcq:
            config["prompts"]["stage2_build_mcq"]["description"] = (
                request.stage2_build_mcq["description"]
            )

    # Save updated config
    _save_global_config(config)

    # Return updated config
    return await get_prompts_config()

