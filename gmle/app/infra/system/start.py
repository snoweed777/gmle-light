"""GMLE Light サービス起動

サービスの起動を行います。
※ AnkiはローカルMacで管理するため、Docker内からは起動しません。
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any, Dict

from .config import PID_FILES, SERVICES
from .status import get_service_status


def start_service(service_name: str, scripts_dir: Path | None = None) -> Dict[str, Any]:
    """サービスを起動"""
    if service_name not in SERVICES:
        return {
            "name": service_name,
            "status": "error",
            "error": f"Unknown service: {service_name}",
        }
    
    # Ankiはローカル管理のため、Docker内からは起動しない
    if service_name == "anki":
        return {
            "name": service_name,
            "status": "error",
            "error": "Anki is managed locally on Mac. Please start Anki with AnkiConnect manually.",
        }
    
    current_status = get_service_status(service_name)
    if current_status["status"] == "running":
        return current_status
    
    service_config = SERVICES[service_name]
    
    # scripts_dirが指定されていない場合は、プロジェクトルートから推測
    if scripts_dir is None:
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent.parent
        scripts_dir = project_root / "scripts" / "service"
    else:
        scripts_dir = Path(scripts_dir)
    
    project_root = scripts_dir.parent.parent
    
    try:
        script_name: str | None = service_config.get("script")
        if script_name is not None:
            script = scripts_dir / script_name
            if not script.exists():
                return {
                    "name": service_name,
                    "status": "error",
                    "error": f"Start script not found: {script}",
                }
            subprocess.Popen(
                ["bash", str(script)],
                cwd=str(project_root),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif service_name == "gui":
            frontend_dir = project_root / "frontend"
            process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=str(frontend_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            pid_file = PID_FILES.get("gui")
            if pid_file:
                with open(pid_file, "w") as f:
                    f.write(str(process.pid))
        else:
            return {
                "name": service_name,
                "status": "error",
                "error": f"Start method not defined for: {service_name}",
            }
        
        timeout: int = service_config.get("start_timeout", 15)
        for _ in range(timeout):
            time.sleep(1)
            status = get_service_status(service_name)
            if status["status"] == "running":
                return status
        
        return get_service_status(service_name)
        
    except Exception as e:
        return {
            "name": service_name,
            "status": "error",
            "error": f"Failed to start: {e}",
        }
