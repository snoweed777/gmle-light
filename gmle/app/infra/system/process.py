"""GMLE+ プロセス基本操作

PID取得・プロセス確認・PID検出を行います。
"""

from __future__ import annotations

import os
import re
import subprocess
from typing import Optional


def get_pid(pid_file: str) -> Optional[int]:
    """PIDファイルからPIDを取得"""
    if not os.path.exists(pid_file):
        return None
    try:
        with open(pid_file, "r") as f:
            pid_str = f.read().strip()
            return int(pid_str) if pid_str else None
    except (ValueError, IOError):
        return None


def is_process_running(pid: int) -> bool:
    """プロセスが実行中か確認"""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def find_pid_by_port(port: int) -> Optional[int]:
    """ポートを使用しているプロセスのPIDを検出"""
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split("\n")
            for pid_str in pids:
                try:
                    pid = int(pid_str.strip())
                    if is_process_running(pid):
                        return pid
                except ValueError:
                    pass
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass
    
    try:
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0 and f":{port}" in result.stdout:
            for line in result.stdout.split("\n"):
                if f":{port}" in line:
                    match = re.search(r'pid=(\d+)', line)
                    if match:
                        pid = int(match.group(1))
                        if is_process_running(pid):
                            return pid
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


def find_pid_by_process_pattern(pattern: str) -> Optional[int]:
    """プロセス名パターンでPIDを検出"""
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=2
        )
        pattern_lower = pattern.lower()
        for line in result.stdout.split("\n"):
            line_lower = line.lower()
            if pattern_lower in line_lower:
                parts = line.split()
                if len(parts) > 1:
                    try:
                        pid = int(parts[1])
                        if is_process_running(pid):
                            return pid
                    except (ValueError, IndexError):
                        pass
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass
    return None

