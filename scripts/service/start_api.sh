#!/bin/bash
# Start GMLE+ REST API server

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

# Set default values
HOST="${GMLE_API_HOST:-0.0.0.0}"
PORT="${GMLE_API_PORT:-8000}"
WORKERS="${GMLE_API_WORKERS:-1}"

# Python実行ファイルの決定（仮想環境があれば使用）
# Check /opt/venv first (Docker container), then /app/venv, then local venv
if [ -d "/opt/venv" ] && [ -f "/opt/venv/bin/python3" ]; then
    PYTHON_CMD="/opt/venv/bin/python3"
    UVICORN_CMD="/opt/venv/bin/uvicorn"
elif [ -d "/app/venv" ] && [ -f "/app/venv/bin/python3" ]; then
    PYTHON_CMD="/app/venv/bin/python3"
    UVICORN_CMD="/app/venv/bin/uvicorn"
elif [ -d "venv" ] && [ -f "venv/bin/python3" ]; then
    PYTHON_CMD="venv/bin/python3"
    UVICORN_CMD="venv/bin/uvicorn"
else
    PYTHON_CMD="python3"
    UVICORN_CMD="uvicorn"
fi

# PIDファイルパス
PID_FILE="/tmp/gmle-api.pid"

# 既に起動している場合は終了（プロセスが実際に存在する場合のみ）
if [ -f "${PID_FILE}" ]; then
    OLD_PID=$(cat "${PID_FILE}" 2>/dev/null || echo "")
    # プロセスが存在し、かつuvicornプロセスである場合のみスキップ
    if [ -n "${OLD_PID}" ] && ps -p "${OLD_PID}" > /dev/null 2>&1; then
        # プロセスが実際にuvicornかどうか確認
        if ps -p "${OLD_PID}" -o cmd | grep -q "uvicorn.*rest.main"; then
            echo "API is already running (PID: ${OLD_PID})"
            exit 0
        fi
    fi
    # プロセスが存在しない、またはuvicornでない場合はPIDファイルを削除
    rm -f "${PID_FILE}"
fi

# ポートが使用中の場合、既存のプロセスを停止
if command -v lsof >/dev/null 2>&1; then
    EXISTING_PID=$(lsof -ti :${PORT} 2>/dev/null | head -1)
    if [ -n "${EXISTING_PID}" ]; then
        echo "Port ${PORT} is already in use (PID: ${EXISTING_PID}), stopping..."
        kill -9 "${EXISTING_PID}" 2>/dev/null || true
        sleep 2
    fi
else
    # lsofが利用できない場合は、psコマンドでuvicornプロセスを検索
    EXISTING_PID=$(ps aux | grep "uvicorn.*gmle.app.api.rest.main" | grep -v grep | awk '{print $2}' | head -1)
    if [ -n "${EXISTING_PID}" ]; then
        echo "Found existing uvicorn process (PID: ${EXISTING_PID}), stopping..."
        kill -9 "${EXISTING_PID}" 2>/dev/null || true
        sleep 2
    fi
fi

# PYTHONPATHを設定（プロジェクトルートを追加）
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

# --reloadオプションは開発環境でのみ使用（環境変数で制御）
RELOAD_OPTION=""
if [ "${GMLE_API_RELOAD:-true}" = "true" ]; then
    RELOAD_OPTION="--reload"
fi

# Start uvicorn server
cd "$PROJECT_ROOT"
# PYTHONPATHを環境変数として明示的に設定してから実行
env PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}" ${UVICORN_CMD} gmle.app.api.rest.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    ${RELOAD_OPTION} &
API_PID=$!

# まず親プロセスのPIDを保存
echo "${API_PID}" > "${PID_FILE}"

# --reloadオプション使用時は、実際にリスニングしているプロセスのPIDを取得
if [ -n "${RELOAD_OPTION}" ]; then
    # サーバーが起動するまで待機（最大10秒）
    MAX_WAIT=10
    WAIT_COUNT=0
    
    while [ ${WAIT_COUNT} -lt ${MAX_WAIT} ]; do
        # ヘルスチェックでサーバーが起動したか確認
        if curl -s "http://localhost:${PORT}/health" > /dev/null 2>&1; then
            # pgrep/pgrepでuvicornプロセスのPIDを取得（親プロセスを除外）
            REAL_PID=$(pgrep -f "uvicorn.*rest.main" 2>/dev/null | grep -v "^${API_PID}$" | head -1)
            if [ -n "${REAL_PID}" ] && ps -p "${REAL_PID}" > /dev/null 2>&1; then
                echo "${REAL_PID}" > "${PID_FILE}"
                API_PID=${REAL_PID}
            fi
            break
        fi
        sleep 1
        WAIT_COUNT=$((WAIT_COUNT + 1))
    done
fi

# バックグラウンド実行の場合はwaitしない（環境変数で制御）
if [ "${GMLE_API_FOREGROUND:-false}" = "true" ]; then
    # フォアグラウンド実行の場合のみwait
    wait
else
    # バックグラウンド実行の場合はヘルスチェックで起動確認
    MAX_WAIT=15
    WAIT_COUNT=0
    while [ ${WAIT_COUNT} -lt ${MAX_WAIT} ]; do
        # プロセスが存在するか確認
        if ! ps -p "${API_PID}" > /dev/null 2>&1; then
            echo "ERROR: API process died unexpectedly"
            rm -f "${PID_FILE}"
            exit 1
        fi
        # ヘルスチェックで起動確認
        if curl -s "http://localhost:${PORT}/health" > /dev/null 2>&1; then
            echo "API started in background (PID: ${API_PID}, port: ${PORT})"
            # PIDファイルが確実に存在することを確認
            if [ -f "${PID_FILE}" ]; then
                exit 0
            else
                echo "WARNING: PID file was removed, recreating..."
                echo "${API_PID}" > "${PID_FILE}"
                exit 0
            fi
        fi
        sleep 1
        WAIT_COUNT=$((WAIT_COUNT + 1))
    done
    
    # タイムアウトした場合でもプロセスが存在すれば成功とする
    if ps -p "${API_PID}" > /dev/null 2>&1; then
        echo "API started in background (PID: ${API_PID}), but health check timeout (may still be starting)"
        # PIDファイルが確実に存在することを確認
        if [ ! -f "${PID_FILE}" ]; then
            echo "${API_PID}" > "${PID_FILE}"
        fi
    else
        echo "ERROR: API process failed to start"
        rm -f "${PID_FILE}"
        exit 1
    fi
fi

