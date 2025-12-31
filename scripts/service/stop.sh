#!/bin/bash
# GMLE+ サービス停止スクリプト（簡略版）
# 共通ライブラリを使用してシンプルに実装

set -e

# 共通ライブラリを読み込み
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/service_common.sh"

# サービスを停止
stop_service() {
    local service_name=$1
    local pid_file=$2
    local process_pattern=$3
    
    # PIDファイルが存在しない
    if [ ! -f "$pid_file" ]; then
        log "$service_name is not running (PID file not found)"
        return 0
    fi
    
    # PIDを検証
    local pid
    pid=$(validate_pid "$pid_file" "$process_pattern" 2>/dev/null)
    
    if [ -z "$pid" ]; then
        log "$service_name is not running (invalid PID file)"
        rm -f "$pid_file"
        return 0
    fi
    
    # プロセスを停止
    log "Stopping $service_name (PID: $pid)..."
    if stop_process "$pid"; then
        rm -f "$pid_file"
        log "$service_name stopped"
    else
        log "WARNING: Failed to stop $service_name gracefully"
        # プロセス名で検索して停止（子プロセスも含む）
        if [ -n "$process_pattern" ]; then
            pkill -f "$process_pattern" 2>/dev/null || true
        fi
        rm -f "$pid_file"
        log "$service_name force stopped"
    fi
}

# メイン処理
main() {
    log "=== GMLE+ Shutdown ==="
    
    # GUI停止
    stop_service "GUI" "$GUI_PID_FILE" "vite"
    
    # API停止
    stop_service "API" "$API_PID_FILE" "uvicorn.*gmle.app.api.rest.main"
    
    # Anki停止（複数のPIDファイルをチェック）
    if [ -f "/tmp/anki-headless.pid" ]; then
        stop_service "Anki" "/tmp/anki-headless.pid" "anki"
    fi
    if [ -f "$ANKI_PID_FILE" ]; then
        stop_service "Anki" "$ANKI_PID_FILE" "anki"
    fi
    
    # Xvfb停止
    if [ -f "$XVFB_PID_FILE" ]; then
        stop_service "Xvfb" "$XVFB_PID_FILE" "Xvfb"
    fi
    
    log "=== Shutdown Complete ==="
}

main "$@"

