#!/bin/bash
# GMLE Light Docker Entrypoint
# Anki/AnkiConnectはローカルMacで管理（Docker外）

set -e

log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $*"
}

log_warn() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN] $*" >&2
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $*" >&2
}

# Activate Python virtual environment
if [ -d "/app/venv" ]; then
    source /app/venv/bin/activate
    log_info "Python venv activated"
elif [ -d "/opt/venv" ]; then
    source /opt/venv/bin/activate
    log_info "Python venv activated (from /opt/venv)"
else
    log_warn "No Python venv found, using system Python"
fi

# Check AnkiConnect availability (on host Mac)
check_ankiconnect() {
    log_info "Checking AnkiConnect availability on host Mac..."
    if curl -s --max-time 5 -X POST http://host.docker.internal:8765 \
        -H "Content-Type: application/json" \
        -d '{"action":"version","version":6}' > /dev/null 2>&1; then
        log_info "✅ AnkiConnect is available on host Mac"
        return 0
    else
        log_warn "⚠️ AnkiConnect is not available on host Mac"
        log_warn "Please start Anki with AnkiConnect addon on your Mac"
        return 1
    fi
}

# Start REST API
start_api() {
    log_info "Starting REST API server..."
    cd /app
    if [ -f "/app/scripts/service/start_api.sh" ]; then
        bash /app/scripts/service/start_api.sh &
    else
        uvicorn gmle.app.api.rest.main:app --host 0.0.0.0 --port 8000 &
    fi
    log_info "REST API server started on port 8000"
}

# Start GUI server
start_gui() {
    log_info "Starting GUI server..."
    cd /app/frontend
    if [ -d "node_modules" ] || [ -L "node_modules" ]; then
        npm run dev -- --host 0.0.0.0 --port 3001 &
        log_info "GUI server started on port 3001"
    else
        log_warn "node_modules not found, skipping GUI server"
    fi
}

# Main
main() {
    log_info "=== GMLE Light Starting ==="
    
    # Check AnkiConnect (non-blocking)
    check_ankiconnect || true
    
    # Start services
    start_api
    sleep 2
    start_gui
    
    log_info "=== GMLE Light Ready ==="
    log_info "REST API: http://localhost:8000"
    log_info "GUI: http://localhost:3001"
    log_info "AnkiConnect: http://host.docker.internal:8765 (on host Mac)"
    
    # Keep container running
    if [ "$#" -gt 0 ]; then
        exec "$@"
    else
        # Wait for any process to exit
        wait -n
    fi
}

main "$@"

