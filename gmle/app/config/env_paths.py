"""Environment-based path resolution for robust configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def get_project_root() -> Path:
    """Get project root directory from environment or fallback to cwd."""
    if project_root := os.getenv("GMLE_PROJECT_ROOT"):
        return Path(project_root)
    
    # Try to find project root by looking for marker files
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        # Check for project markers
        if (parent / "pyproject.toml").exists() or (parent / "gmle").exists():
            return parent
    
    # Fallback to current directory
    return current


def get_config_dir() -> Path:
    """Get config directory from environment or fallback to default."""
    if config_dir := os.getenv("GMLE_CONFIG_DIR"):
        return Path(config_dir)
    
    # Try multiple possible paths in order of preference
    project_root = get_project_root()
    possible_paths = [
        project_root / "config",
        Path("/app/config"),  # Docker default
        Path.cwd() / "config",
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # Fallback to first option (will be created if needed)
    return possible_paths[0]


def get_spaces_config_dir() -> Path:
    """Get spaces config directory."""
    if spaces_dir := os.getenv("GMLE_SPACES_DIR"):
        return Path(spaces_dir)
    
    return get_config_dir() / "spaces"


def get_data_dir() -> Path:
    """Get data directory from environment or fallback to default."""
    if data_dir := os.getenv("GMLE_DATA_DIR"):
        return Path(data_dir)
    
    return get_project_root() / "data"


def get_sources_dir() -> Path:
    """Get sources directory from environment or fallback to default."""
    if sources_dir := os.getenv("GMLE_SOURCES_DIR"):
        return Path(sources_dir)
    
    return get_project_root() / "sources"


def resolve_config_path(
    filename: str,
    subdir: Optional[str] = None,
) -> Optional[Path]:
    """
    Resolve a config file path, trying multiple locations.
    
    Args:
        filename: Name of the config file (e.g., "gmle.yaml")
        subdir: Optional subdirectory under config (e.g., "spaces")
    
    Returns:
        Path to the config file if found, None otherwise
    """
    config_dir = get_config_dir()
    
    if subdir:
        search_dir = config_dir / subdir
    else:
        search_dir = config_dir
    
    config_path = search_dir / filename
    
    if config_path.exists():
        return config_path
    
    return None

