"""Environment health check utilities."""

from __future__ import annotations

import sys
from typing import Any, Dict, List

from gmle.app.config.env_paths import (
    get_config_dir,
    get_data_dir,
    get_project_root,
    get_sources_dir,
    get_spaces_config_dir,
)


class HealthCheckIssue:
    """Represents a health check issue."""

    def __init__(
        self,
        severity: str,
        category: str,
        message: str,
        suggestion: str = "",
    ):
        self.severity = severity  # "error", "warning", "info"
        self.category = category  # "dependency", "path", "config", "permission"
        self.message = message
        self.suggestion = suggestion

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "suggestion": self.suggestion,
        }


def check_python_dependencies() -> List[HealthCheckIssue]:
    """Check if required Python modules are available."""
    issues = []
    
    required_modules = [
        ("yaml", "PyYAML", "pip install pyyaml"),
        ("fastapi", "FastAPI", "pip install fastapi"),
        ("httpx", "httpx", "pip install httpx"),
        ("uvicorn", "uvicorn", "pip install uvicorn"),
        ("typer", "typer", "pip install typer"),
    ]
    
    for module_name, display_name, install_cmd in required_modules:
        try:
            __import__(module_name)
        except ImportError:
            issues.append(HealthCheckIssue(
                severity="error",
                category="dependency",
                message=f"Required module '{display_name}' is not installed",
                suggestion=f"Install with: {install_cmd}",
            ))
    
    return issues


def check_directories() -> List[HealthCheckIssue]:
    """Check if required directories exist and are accessible."""
    issues = []
    
    # Check project root
    project_root = get_project_root()
    if not project_root.exists():
        issues.append(HealthCheckIssue(
            severity="error",
            category="path",
            message=f"Project root not found: {project_root}",
            suggestion="Set GMLE_PROJECT_ROOT environment variable",
        ))
    
    # Check config directory
    config_dir = get_config_dir()
    if not config_dir.exists():
        issues.append(HealthCheckIssue(
            severity="error",
            category="path",
            message=f"Config directory not found: {config_dir}",
            suggestion="Set GMLE_CONFIG_DIR environment variable or create config/ directory",
        ))
    
    # Check spaces config directory
    spaces_dir = get_spaces_config_dir()
    if not spaces_dir.exists():
        issues.append(HealthCheckIssue(
            severity="warning",
            category="path",
            message=f"Spaces config directory not found: {spaces_dir}",
            suggestion="Create config/spaces/ directory and add space configuration files",
        ))
    elif not list(spaces_dir.glob("*.yaml")):
        issues.append(HealthCheckIssue(
            severity="warning",
            category="config",
            message="No space configuration files found",
            suggestion="Add at least one .yaml file to config/spaces/",
        ))
    
    # Check data directory
    data_dir = get_data_dir()
    if not data_dir.exists():
        issues.append(HealthCheckIssue(
            severity="info",
            category="path",
            message=f"Data directory not found: {data_dir}",
            suggestion="Data directory will be created automatically when needed",
        ))
    
    # Check sources directory
    sources_dir = get_sources_dir()
    if not sources_dir.exists():
        issues.append(HealthCheckIssue(
            severity="info",
            category="path",
            message=f"Sources directory not found: {sources_dir}",
            suggestion="Sources directory will be created automatically when needed",
        ))
    
    return issues


def check_permissions() -> List[HealthCheckIssue]:
    """Check if we have necessary permissions."""
    issues = []
    
    config_dir = get_config_dir()
    if config_dir.exists():
        # Check read permission
        if not config_dir.is_dir():
            issues.append(HealthCheckIssue(
                severity="error",
                category="permission",
                message=f"Config path exists but is not a directory: {config_dir}",
                suggestion="Remove or rename the conflicting file",
            ))
        elif not (config_dir / ".").exists():
            issues.append(HealthCheckIssue(
                severity="error",
                category="permission",
                message=f"No read permission for config directory: {config_dir}",
                suggestion="Check directory permissions",
            ))
    
    return issues


def check_environment() -> Dict[str, Any]:
    """
    Run all health checks and return a summary.
    
    Returns:
        Dictionary with:
        - healthy: bool (True if no errors)
        - issues: List of issue dictionaries
        - summary: Summary statistics
    """
    all_issues: List[HealthCheckIssue] = []
    
    # Run all checks
    all_issues.extend(check_python_dependencies())
    all_issues.extend(check_directories())
    all_issues.extend(check_permissions())
    
    # Count by severity
    errors = [i for i in all_issues if i.severity == "error"]
    warnings = [i for i in all_issues if i.severity == "warning"]
    infos = [i for i in all_issues if i.severity == "info"]
    
    # Determine overall health
    healthy = len(errors) == 0
    
    return {
        "healthy": healthy,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "project_root": str(get_project_root()),
        "config_dir": str(get_config_dir()),
        "spaces_dir": str(get_spaces_config_dir()),
        "issues": [issue.to_dict() for issue in all_issues],
        "summary": {
            "total": len(all_issues),
            "errors": len(errors),
            "warnings": len(warnings),
            "infos": len(infos),
        },
    }



