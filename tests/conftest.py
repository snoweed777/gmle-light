"""Pytest configuration for GMLE Light tests."""

import pytest


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory for tests."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    spaces_dir = config_dir / "spaces"
    spaces_dir.mkdir()
    return config_dir


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory for tests."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir

