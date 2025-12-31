"""Internal API implementation for Ingest."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from gmle.app.ingest.readwise import ingest_readwise as _ingest_readwise
from gmle.app.ingest.textfile import ingest_textfile as _ingest_textfile
from .base import IngestAPI


class InternalIngestAPI(IngestAPI):
    """Internal implementation of Ingest API (monolithic)."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Ingest API.
        
        Args:
            config: Optional config dict
        """
        self.config = config
    
    def ingest_readwise(self, space_id: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Ingest from Readwise using internal implementation."""
        return _ingest_readwise(space_id, params=params, config=self.config)
    
    def ingest_textfile(self, file_path: str, title: Optional[str] = None) -> List[Dict[str, Any]]:
        """Ingest from text file using internal implementation."""
        return _ingest_textfile(file_path, title=title)
    
    def ingest_uploaded_file(
        self,
        file_content: bytes,
        filename: str,
        title: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Ingest from uploaded file content."""
        suffix = Path(filename).suffix.lower()
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=suffix, delete=False
        ) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name
        
        try:
            return _ingest_textfile(tmp_path, title=title)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


def get_ingest_api(config: Optional[Dict[str, Any]] = None) -> IngestAPI:
    """Get Ingest API instance.
    
    Args:
        config: Configuration dictionary (optional)
        
    Returns:
        Ingest API instance
        
    Note:
        Currently returns internal implementation.
        In the future, can return microservice implementation based on config.
    """
    # Check if microservice mode is enabled
    if config and config.get("api", {}).get("ingest", {}).get("microservice", {}).get("enabled", False):
        # Future: Return microservice implementation
        # return MicroserviceIngestAPI(config["api"]["ingest"]["microservice"]["url"])
        pass
    
    # Default: Return internal implementation
    return InternalIngestAPI(config=config)

