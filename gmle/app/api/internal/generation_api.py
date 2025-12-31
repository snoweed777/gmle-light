"""Internal API implementation for MCQ generation."""

from __future__ import annotations

from typing import Any, Dict, Optional

from gmle.app.generate.generator import generate_mcq as _generate_mcq
from .base import GenerationAPI


class InternalGenerationAPI(GenerationAPI):
    """Internal implementation of Generation API (monolithic)."""
    
    def generate_mcq(self, source: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any] | None:
        """Generate MCQ from source using internal implementation."""
        return _generate_mcq(source, config=config)


def get_generation_api(config: Optional[Dict[str, Any]] = None) -> GenerationAPI:
    """Get Generation API instance.
    
    Args:
        config: Configuration dictionary (optional)
        
    Returns:
        Generation API instance
        
    Note:
        Currently returns internal implementation.
        In the future, can return microservice implementation based on config.
    """
    # Check if microservice mode is enabled
    if config and config.get("api", {}).get("generation", {}).get("microservice", {}).get("enabled", False):
        # Future: Return microservice implementation
        # return MicroserviceGenerationAPI(config["api"]["generation"]["microservice"]["url"])
        pass
    
    # Default: Return internal implementation
    return InternalGenerationAPI()

