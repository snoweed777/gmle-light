"""Environment variable management for .env file."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from gmle.app.config.env_paths import get_project_root


def _get_env_file() -> Path:
    """Get .env file path using project root detection."""
    project_root = get_project_root()
    env_file = project_root / ".env"
    if env_file.exists():
        return env_file
    # Fallback to current directory
    return Path(".env")


class SecretsManager:
    """Manage environment variables in .env file."""

    def __init__(self):
        """Initialize SecretsManager."""
        # Ensure .env file is loaded
        env_file = _get_env_file()
        if env_file.exists():
            load_dotenv(env_file, override=False)

    def get_secret(self, key: str, default: str | None = None) -> str | None:
        """Get a single secret by key from environment variables.

        Args:
            key: Secret key
            default: Default value if not found

        Returns:
            Secret value or default
        """
        # Reload .env file to get latest values
        env_file = _get_env_file()
        if env_file.exists():
            load_dotenv(env_file, override=True)
        
        # Check environment variable (loaded from .env file)
        env_key = key.upper()
        env_value = os.getenv(env_key)
        if env_value:
            return env_value

        return default

    def set_secret(self, key: str, value: str) -> None:
        """Set a single secret.

        Saves to .env file only (same pattern as LLM API keys).

        Args:
            key: Secret key
            value: Secret value
        """
        # Save to .env file only
        env_file = _get_env_file()
        env_key = key.upper()
        
        if env_file.exists():
            # Read existing .env file
            lines = []
            key_found = False
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line_stripped = line.rstrip()
                    # Check if this line contains the key
                    if line_stripped.startswith(f"{env_key}="):
                        lines.append(f"{env_key}={value}\n")
                        key_found = True
                    else:
                        lines.append(line)  # Keep original line ending
            
            # If key not found, append it
            if not key_found:
                lines.append(f"{env_key}={value}\n")
            
            # Write back to .env file
            with open(env_file, "w", encoding="utf-8") as f:
                f.writelines(lines)
        else:
            # Create new .env file
            env_file.parent.mkdir(parents=True, exist_ok=True)
            with open(env_file, "w", encoding="utf-8") as f:
                f.write(f"{env_key}={value}\n")
            env_file.chmod(0o600)

