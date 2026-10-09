#!/usr/bin/env bash
# Runs both AG-UI backend (:8000) and CopilotKit frontend (:3000) in a single command.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Trap Ctrl+C / exit to ensure both processes are terminated cleanly
cleanup() {
  echo ""
  echo "Stopping backend and frontend processes..."
  kill $(jobs -p) 2>/dev/null || true
  wait 2>/dev/null || true
  echo "Done."
}
trap cleanup EXIT INT TERM

echo "Starting backend (FastAPI / ADK) on :8000..."
(cd "$ROOT_DIR" && uv sync && exec uv run uvicorn backend.main:app --port 8000 --reload) &

echo "Starting frontend (Next.js / CopilotKit) on :3000..."
(cd "$ROOT_DIR/frontend" && exec npm run dev) &

wait
