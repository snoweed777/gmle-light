"""GMLE+ サービス起動

サービスの起動を行います。
"""

from __future__ import annotations

import shutil
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
            # Ankiの場合はnohupでバックグラウンド実行
            if service_name == "anki":
                # Ankiがインストールされているか事前確認
                if not shutil.which("anki"):
                    return {
                        "name": service_name,
                        "status": "error",
                        "error": "Anki is not installed. Please run: bash scripts/setup/setup.sh",
                    }
                subprocess.Popen(
                    ["nohup", "bash", str(script)],
                    cwd=str(project_root),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                # Ankiは起動に時間がかかるため、すぐに状態を返す
                return {
                    "name": service_name,
                    "status": "stopped",
                    "pid": None,
                    "port": service_config.get("port"),
                    "health_check": service_config.get("health_check"),
                    "message": "Anki is starting in the background. Please check status in a few seconds.",
                }
            else:
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
        
        # タイムアウト後も起動していない場合、エラーログを確認
        final_status = get_service_status(service_name)
        if final_status["status"] != "running" and service_name == "anki":
            # Ankiのログファイルを確認
            log_file = Path.home() / ".local" / "share" / "Anki2" / "anki-headless.log"
            if log_file.exists():
                try:
                    with open(log_file, "r") as f:
                        log_lines = f.readlines()
                        # 最後のエラーメッセージを取得
                        for line in reversed(log_lines[-30:]):
                            if "ERROR" in line or "Failed" in line or "not installed" in line:
                                error_msg = line.strip()
                                # タイムスタンプを除去してエラーメッセージのみを取得
                                if "] " in error_msg:
                                    error_msg = error_msg.split("] ", 1)[1]
                                final_status["error"] = error_msg
                                break
                except Exception:
                    pass
        
        return final_status
        
    except Exception as e:
        return {
            "name": service_name,
            "status": "error",
            "error": f"Failed to start: {e}",
        }

