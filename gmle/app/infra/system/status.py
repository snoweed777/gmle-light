"""GMLE+ 状態確認

サービスの状態確認を行います。
"""

from __future__ import annotations

import os
import socket
from typing import Any, Dict
from urllib.error import URLError
from urllib.request import urlopen

from .config import PID_FILES, SERVICES
from .process import (
    find_pid_by_port,
    find_pid_by_process_pattern,
    get_pid,
    is_process_running,
)


def check_port(port: int) -> bool:
    """ポートがリスニング中か確認"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()
        return result == 0
    except Exception:
        return False


def check_health(url: str) -> bool:
    """ヘルスチェック"""
    try:
        with urlopen(url, timeout=2) as response:
            code: int = response.getcode()
            return code == 200
    except (URLError, OSError, ValueError):
        return False


def get_service_status(service_name: str) -> Dict[str, Any]:
    """サービス状態を取得"""
    if service_name not in SERVICES:
        return {
            "name": service_name,
            "status": "unknown",
            "error": f"Unknown service: {service_name}"
        }
    service_config = SERVICES[service_name]
    pid_file = PID_FILES.get(service_name)
    status = {
        "name": service_name,
        "status": "stopped",
        "pid": None,
        "port": service_config.get("port"),
        "health_check": service_config.get("health_check")
    }
    pid = None
    if pid_file:
        pid = get_pid(pid_file)
        if pid is not None and not is_process_running(pid):
            if os.path.exists(pid_file):
                os.remove(pid_file)
            pid = None
    port: int | None = service_config.get("port")
    port_listening = check_port(port) if port is not None else False
    
    def save_pid(found_pid: int) -> None:
        if pid_file:
            with open(pid_file, "w") as f:
                f.write(str(found_pid))
    
    if port_listening:
        status["status"] = "running"
        if pid is None and port is not None:
            found_pid = find_pid_by_port(port)
            if found_pid:
                pid = found_pid
                save_pid(pid)
        process_pattern: str | None = service_config.get("process_pattern")
        if pid is None and process_pattern is not None:
            found_pid = find_pid_by_process_pattern(process_pattern)
            if found_pid:
                pid = found_pid
                save_pid(pid)
        if pid:
            status["pid"] = pid
        return status
    if pid is not None:
        status["status"] = "warning"
        status["warning"] = f"Port {service_config.get('port')} not listening"
        status["pid"] = pid
        return status
    health_check: str | None = service_config.get("health_check")
    if health_check is not None and check_health(health_check):
        status["status"] = "running"
        if port is not None:
            found_pid = find_pid_by_port(port)
            if found_pid:
                status["pid"] = found_pid
                save_pid(found_pid)
        return status
    return status


def get_all_status() -> Dict[str, Any]:
    """全サービスの状態を取得"""
    services = {}
    for service_name in SERVICES.keys():
        services[service_name] = get_service_status(service_name)
    return {"services": services}

