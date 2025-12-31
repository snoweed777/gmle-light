#!/bin/bash
# GMLE+ サービス状態確認スクリプト（簡略版）
# 共通ライブラリを使用してシンプルに実装

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

# メイン処理
main() {
    echo "=== GMLE+ Service Status ==="
    echo ""
    
    # Anki確認（複数のPIDファイルをチェック）
    local anki_running=false
    if [ -f "/tmp/anki-headless.pid" ]; then
        local status
        status=$(get_service_status "Anki" "/tmp/anki-headless.pid" "8765" "http://127.0.0.1:8765")
        if [ "$status" = "running" ]; then
            local pid
            pid=$(validate_pid "/tmp/anki-headless.pid" 2>/dev/null)
            echo "  Anki: ✅ Running (PID: ${pid})"
            anki_running=true
        else
            check_service "Anki" "/tmp/anki-headless.pid" "8765" "http://127.0.0.1:8765"
        fi
    elif [ -f "$ANKI_PID_FILE" ]; then
        local status
        status=$(get_service_status "Anki" "$ANKI_PID_FILE" "8765" "http://127.0.0.1:8765")
        if [ "$status" = "running" ]; then
            anki_running=true
        fi
        check_service "Anki" "$ANKI_PID_FILE" "8765" "http://127.0.0.1:8765"
    else
        echo "  Anki: ❌ Not running"
    fi
    
    # Xvfb確認（Ankiが起動している場合のみ）
    if [ "$anki_running" = "true" ] && [ -f "$XVFB_PID_FILE" ]; then
        check_service "Xvfb" "$XVFB_PID_FILE" "" ""
    fi
    
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

