#!/usr/bin/env bash
set -euo pipefail

# DefinitieAgent Launcher
# Called by the macOS .app bundle — not intended for direct terminal use.
# For terminal use, run: streamlit run src/main.py

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_DIR"

LOG_FILE="/tmp/definitieagent.log"

# Activate virtual environment
if [[ ! -d .venv ]]; then
    echo "Error: .venv not found in $PROJECT_DIR" >> "$LOG_FILE"
    exit 1
fi
source .venv/bin/activate

# Start Streamlit in background (headless = no auto-browser from streamlit)
streamlit run src/main.py --server.headless=true >> "$LOG_FILE" 2>&1 &
STREAMLIT_PID=$!

# Wait for server to be ready, then open browser
for i in {1..30}; do
    if curl -s http://localhost:8501 > /dev/null 2>&1; then
        open "http://localhost:8501"
        break
    fi
    sleep 1
done

# Keep running until Streamlit exits (keeps .app active in Dock)
wait $STREAMLIT_PID
