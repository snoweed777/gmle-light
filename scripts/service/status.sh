#!/bin/bash
# GMLE Light サービス状態確認スクリプト
# GUI と API サービスの状態を確認

set -e

# 共通ライブラリを読み込み
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/service_common.sh"

# サービス状態を表示
check_service() {
    local name=$1
    local pid_file=$2
    local port=$3
    local health_url=$4
    
    echo -n "  ${name}: "
    
    local status
    status=$(get_service_status "$name" "$pid_file" "$port" "$health_url")
    
    case "$status" in
        "running")
            local pid
            pid=$(validate_pid "$pid_file" 2>/dev/null)
            echo "✅ Running (PID: ${pid})"
            ;;
        "unhealthy")
            local pid
            pid=$(validate_pid "$pid_file" 2>/dev/null)
            if [ -n "$port" ]; then
                echo "⚠️  Process running (PID: ${pid}) but port ${port} not listening"
            else
                echo "⚠️  Process running (PID: ${pid}) but health check failed"
            fi
            ;;
        *)
            echo "❌ Not running"
            # 無効なPIDファイルを削除
            [ -f "$pid_file" ] && rm -f "$pid_file"
            ;;
    esac
}

# AnkiConnect接続確認（ローカルMac）
check_anki_connect() {
    echo -n "  AnkiConnect (Mac): "
    
    # host.docker.internal経由でMacのAnkiConnectに接続
    local anki_url="http://host.docker.internal:8765"
    if curl -sf --max-time 3 -X POST "$anki_url" \
        -H "Content-Type: application/json" \
        -d '{"action":"version","version":6}' > /dev/null 2>&1; then
        echo "✅ Connected"
    else
        echo "❌ Not available (ensure Anki is running on Mac with AnkiConnect)"
    fi
}

# メイン処理
main() {
    echo "=== GMLE Light Service Status ==="
    echo ""
    
    # AnkiConnect確認（ローカルMac）
    check_anki_connect
    
    echo ""
    
    # API確認
    check_service "API" "$API_PID_FILE" "8000" "http://localhost:8000/health"
    
    echo ""
    
    # GUI確認
    check_service "GUI" "$GUI_PID_FILE" "3001" "http://localhost:3001"
    
    echo ""
    echo "=== End of Status ==="
}

main "$@"
