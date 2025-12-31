"""Base classes for internal APIs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class GenerationAPI(ABC):
    """Base interface for MCQ generation API."""
    
    @abstractmethod
    def generate_mcq(self, source: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any] | None:
        """Generate MCQ from source.
        
        Args:
            source: Source data with excerpt, title, etc.
            config: Configuration dictionary (optional)
            
        Returns:
            Generated MCQ item or None if generation failed
        """
        pass


class IngestAPI(ABC):
    """Base interface for Ingest API."""
    
    @abstractmethod
    def ingest_readwise(self, space_id: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Ingest from Readwise.
        
        Args:
            space_id: Space ID
            params: Ingest parameters (optional)
            
        Returns:
            List of ingested sources
        """
        pass
    
    @abstractmethod
    def ingest_textfile(self, file_path: str, title: Optional[str] = None) -> List[Dict[str, Any]]:
        """Ingest from text file.
        
        Args:
            file_path: Path to text file
            title: Optional title for the source
            
        Returns:
            List of ingested sources
        """
        pass
    
    @abstractmethod
    def ingest_uploaded_file(
        self,
        file_content: bytes,
        filename: str,
        title: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Ingest from uploaded file content.
        
        Args:
            file_content: File content as bytes
            filename: Original filename (for format detection)
            title: Optional title for the source
            
        Returns:
            List of ingested sources
        """
        pass


class SystemAPI(ABC):
    """Base interface for System Management API."""
    
    @abstractmethod
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Get service status.
        
        Args:
            service_name: Service name (anki, api, gui)
            
        Returns:
            Service status dictionary
        """
        pass
    
    @abstractmethod
    def start_service(self, service_name: str) -> Dict[str, Any]:
        """Start service.
        
        Args:
            service_name: Service name (anki, api, gui)
            
        Returns:
            Service status dictionary
        """
        pass
    
    @abstractmethod
    def stop_service(self, service_name: str) -> Dict[str, Any]:
        """Stop service.
        
        Args:
            service_name: Service name (anki, api, gui)
            
        Returns:
            Service status dictionary
        """
        pass
    
    @abstractmethod
    def restart_service(self, service_name: str) -> Dict[str, Any]:
        """Restart service.
        
        Args:
            service_name: Service name (anki, api, gui)
            
        Returns:
            Service status dictionary
        """
        pass
    
    @abstractmethod
    def get_all_status(self) -> Dict[str, Any]:
        """Get all services status.
        
        Returns:
            Dictionary with all services status
        """
        pass
