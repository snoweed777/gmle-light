"""YAML configuration file I/O utilities."""

from __future__ import annotations

import shutil
from datetime import datetime
from typing import Any, Dict

import yaml
from fastapi import HTTPException

from gmle.app.config.env_paths import get_config_dir
from gmle.app.infra.errors import ConfigError
from gmle.app.infra.logger import get_logger, log_exception


def load_global_yaml_config() -> Dict[str, Any]:
    """Load global config from gmle.yaml.
    
    Returns:
        Config dictionary
        
    Raises:
        HTTPException: If config file not found or invalid
        ConfigError: If config loading fails
    """
    config_file = get_config_dir() / "gmle.yaml"
    logger = get_logger()
    
    if not config_file.exists():
        logger.warning("Global config file not found", extra={
            "extra_fields": {"config_file": str(config_file)}
        })
        raise HTTPException(status_code=404, detail="Global config not found")
    
    try:
        with config_file.open("r", encoding="utf-8") as f:
            result: Dict[str, Any] = yaml.safe_load(f) or {}
            if not isinstance(result, dict):
                raise ConfigError(f"Global config invalid format: {config_file}")
            return result
    except HTTPException:
        raise
    except Exception as exc:
        log_exception(
            logger,
            "Failed to load global config",
            exc,
            config_file=str(config_file),
        )
        raise ConfigError(f"Failed to load global config: {config_file}") from exc


def save_global_yaml_config(config: Dict[str, Any], create_backup: bool = True) -> None:
    """Save global config to gmle.yaml with optional backup.
    
    Args:
        config: Config dictionary to save
        create_backup: Whether to create backup before saving
        
    Raises:
        ConfigError: If config saving fails
    """
    config_file = get_config_dir() / "gmle.yaml"
    logger = get_logger()
    
    try:
        # Create backup if requested and file exists
        if create_backup and config_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = config_file.with_suffix(f".{timestamp}.backup")
            shutil.copy2(config_file, backup_file)
            logger.debug("Created config backup", extra={
                "extra_fields": {
                    "backup_file": str(backup_file),
                }
            })
        
        # Ensure config directory exists
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save updated config
        with config_file.open("w", encoding="utf-8") as f:
            yaml.dump(
                config,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
        
        logger.info("Saved global config", extra={
            "extra_fields": {
                "config_file": str(config_file),
                "backup_created": create_backup and config_file.exists(),
            }
        })
    except Exception as exc:
        log_exception(
            logger,
            "Failed to save global config",
            exc,
            config_file=str(config_file),
        )
        raise ConfigError(f"Failed to save global config: {config_file}") from exc

