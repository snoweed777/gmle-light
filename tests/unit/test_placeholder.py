"""Placeholder test to verify pytest works."""

import pytest


def test_placeholder():
    """Basic test to ensure pytest runs."""
    assert True


@pytest.mark.live
def test_live_placeholder():
    """Placeholder for live tests (skipped in CI)."""
    pytest.skip("Live test placeholder")

