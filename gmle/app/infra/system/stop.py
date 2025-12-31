"""GMLE+ サービス停止

サービスの停止を行います。
"""

from __future__ import annotations

import os
import subprocess
import time
from typing import Any, Dict

from .config import PID_FILES, SERVICES
from .process import get_pid, is_process_running
from .status import get_service_status


def stop_service(service_name: str) -> Dict[str, Any]:
    """サービスを停止"""
    if service_name not in SERVICES:
        return {
            "name": service_name,
            "status": "error",
            "error": f"Unknown service: {service_name}",
        }
    
    pid_file = PID_FILES.get(service_name)
    if not pid_file:
        return get_service_status(service_name)
    
    pid = get_pid(pid_file)
    if pid is None:
        return get_service_status(service_name)
    
    if not is_process_running(pid):
        if os.path.exists(pid_file):
            os.remove(pid_file)
        return get_service_status(service_name)
    
    try:
        os.kill(pid, 15)
        time.sleep(2)
        
        if is_process_running(pid):
            os.kill(pid, 9)
            time.sleep(1)
        
        if os.path.exists(pid_file):
            os.remove(pid_file)
        
        service_config = SERVICES[service_name]
        process_pattern: str | None = service_config.get("process_pattern")
        if process_pattern is not None:
            subprocess.run(["pkill", "-f", process_pattern], capture_output=True)
        
        if service_name == "anki":
            xvfb_pid_file = PID_FILES.get("xvfb")
            if xvfb_pid_file and os.path.exists(xvfb_pid_file):
                xvfb_pid = get_pid(xvfb_pid_file)
                if xvfb_pid and is_process_running(xvfb_pid):
                    os.kill(xvfb_pid, 15)
                if os.path.exists(xvfb_pid_file):
                    os.remove(xvfb_pid_file)
        
        return get_service_status(service_name)
    except Exception as e:
        return {
            "name": service_name,
            "status": "error",
            "error": f"Failed to stop: {e}",
        }

