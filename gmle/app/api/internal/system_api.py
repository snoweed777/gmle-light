"""Internal API implementation for System Management."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from gmle.app.infra.system import (
    get_all_status,
    get_service_status,
    start_service,
    stop_service,
)

from .base import SystemAPI


class InternalSystemAPI(SystemAPI):
    """Internal implementation of System API."""
    
    def __init__(self, scripts_dir: str | None = None):
        """Initialize System API.
        
        Args:
            scripts_dir: Path to scripts/service directory (default: scripts/service/)
        """
        if scripts_dir is None:
            # プロジェクトルートを取得
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent.parent
            scripts_dir = str(project_root / "scripts" / "service")
        self.scripts_dir = Path(scripts_dir)
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Get service status."""
        return get_service_status(service_name)
    
    def get_all_status(self) -> Dict[str, Any]:
        """Get all services status."""
        return get_all_status()
    
    def start_service(self, service_name: str) -> Dict[str, Any]:
        """Start service."""
        return start_service(service_name, scripts_dir=self.scripts_dir)
    
    def stop_service(self, service_name: str) -> Dict[str, Any]:
        """Stop service."""
        return stop_service(service_name)
    
    def restart_service(self, service_name: str) -> Dict[str, Any]:
        """Restart service (stop then start)."""
        # まず停止
        stop_result = self.stop_service(service_name)
        if "error" in stop_result:
            return stop_result
        
        # 停止が成功したら起動
        # 少し待機してから起動（プロセスが完全に終了するのを待つ）
        import time
        time.sleep(2)
        
        return self.start_service(service_name)


def get_system_api(scripts_dir: str | None = None) -> SystemAPI:
    """Get System API instance.
    
    Args:
        scripts_dir: Path to scripts/service directory (optional)
        
    Returns:
        SystemAPI instance
    """
    return InternalSystemAPI(scripts_dir=scripts_dir)
