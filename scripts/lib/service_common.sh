#!/bin/bash
# GMLE+ サービス管理共通ライブラリ
# 各サービス管理スクリプトからsourceで読み込む

# PIDファイルパス定数
readonly PID_DIR="/tmp"
readonly ANKI_PID_FILE="${PID_DIR}/gmle-anki.pid"
readonly API_PID_FILE="${PID_DIR}/gmle-api.pid"
readonly GUI_PID_FILE="${PID_DIR}/gmle-gui.pid"
readonly XVFB_PID_FILE="${PID_DIR}/xvfb-anki.pid"

# ログ関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# PIDファイルからプロセスを検証
# 引数: pid_file [process_pattern]
# 戻り値: PID（成功時）、空文字（失敗時）
validate_pid() {
    local pid_file=$1
    local process_pattern=${2:-}
    
    # PIDファイルが存在しない
    [ -f "$pid_file" ] || return 1
    
    # PIDを読み取り
    local pid
    pid=$(cat "$pid_file" 2>/dev/null || echo "")
    [ -n "$pid" ] || return 1
    
    # プロセスが存在するか確認
    ps -p "$pid" > /dev/null 2>&1 || return 1
    
    # プロセスパターンが指定されている場合は検証
    if [ -n "$process_pattern" ]; then
        ps -p "$pid" -o cmd 2>/dev/null | grep -q "$process_pattern" || return 1
    fi
    
    echo "$pid"
    return 0
}

# プロセスを安全に停止
# 引数: pid [timeout_seconds]
stop_process() {
    local pid=$1
    local timeout=${2:-5}
    
    # プロセスが存在しない場合は成功として扱う
    if ! ps -p "$pid" > /dev/null 2>&1; then
        return 0
    fi
    
    # SIGTERMで停止を試みる
    kill "$pid" 2>/dev/null || return 0
    
    # タイムアウトまで待機
    local count=0
    while [ $count -lt $timeout ]; do
        ps -p "$pid" > /dev/null 2>&1 || return 0
        sleep 1
        count=$((count + 1))
    done
    
    # タイムアウトした場合は強制終了
    kill -9 "$pid" 2>/dev/null || true
    sleep 1
    
    # 最終確認
    if ps -p "$pid" > /dev/null 2>&1; then
        return 1
    fi
    
    return 0
}

# ヘルスチェック
# 引数: url [timeout_seconds]
health_check() {
    local url=$1
    local timeout=${2:-5}
    
    curl -sf --max-time "$timeout" "$url" > /dev/null 2>&1
}

# ポートがリッスンしているか確認
# 引数: port
check_port() {
    local port=$1
    
    # 複数の方法でポートを確認（環境によって利用可能なコマンドが異なる）
    if command -v lsof >/dev/null 2>&1; then
        lsof -i ":$port" 2>/dev/null | grep -q LISTEN && return 0
    fi
    
    if command -v netstat >/dev/null 2>&1; then
        netstat -tlnp 2>/dev/null | grep -q ":${port} " && return 0
    fi
    
    if command -v ss >/dev/null 2>&1; then
        ss -tlnp 2>/dev/null | grep -q ":${port} " && return 0
    fi
    
    return 1
}

# サービス状態を取得
# 引数: service_name pid_file [port] [health_url]
get_service_status() {
    local service_name=$1
    local pid_file=$2
    local port=$3
    local health_url=$4
    
    # PIDファイルが存在しない
    if [ ! -f "$pid_file" ]; then
        echo "not_running"
        return 1
    fi
    
    # PIDを検証
    local pid
    pid=$(validate_pid "$pid_file" 2>/dev/null)
    if [ -z "$pid" ]; then
        echo "not_running"
        return 1
    fi
    
    # ポートチェック
    if [ -n "$port" ] && ! check_port "$port"; then
        echo "unhealthy"
        return 1
    fi
    
    # ヘルスチェック
    if [ -n "$health_url" ] && ! health_check "$health_url"; then
        echo "unhealthy"
        return 1
    fi
    
    echo "running"
    return 0
}

