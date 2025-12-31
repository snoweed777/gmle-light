"""Prompts configuration endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from gmle.app.api.rest.models import (
    PromptInfo,
    PromptsConfigResponse,
    PromptsConfigUpdateRequest,
)
from gmle.app.config.yaml_io import load_global_yaml_config, save_global_yaml_config
from gmle.app.infra.errors import ConfigError
from gmle.app.infra.logger import get_logger, log_exception

router = APIRouter(prefix="/config/prompts", tags=["prompts_config"])


@router.get("", response_model=PromptsConfigResponse)
async def get_prompts_config() -> PromptsConfigResponse:
    """Get prompts configuration."""
    logger = get_logger()
    
    try:
        config = load_global_yaml_config()
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
    except HTTPException:
        raise
    except ConfigError as exc:
        log_exception(logger, "Config error in get_prompts_config", exc)
        raise HTTPException(status_code=500, detail=f"Failed to load prompts config: {str(exc)}")
    except Exception as exc:
        log_exception(logger, "Unexpected error in get_prompts_config", exc)
        raise HTTPException(status_code=500, detail=f"Failed to load prompts config: {str(exc)}")


@router.put("", response_model=PromptsConfigResponse)
async def update_prompts_config(
    request: PromptsConfigUpdateRequest,
) -> PromptsConfigResponse:
    """Update prompts configuration."""
    logger = get_logger()
    
    try:
        config = load_global_yaml_config()

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
        save_global_yaml_config(config)

        # Return updated config
        return await get_prompts_config()
    except HTTPException:
        raise
    except ConfigError as exc:
        log_exception(logger, "Config error in update_prompts_config", exc)
        raise HTTPException(status_code=500, detail=f"Failed to update prompts config: {str(exc)}")
    except Exception as exc:
        log_exception(logger, "Unexpected error in update_prompts_config", exc)
        raise HTTPException(status_code=500, detail=f"Failed to update prompts config: {str(exc)}")

