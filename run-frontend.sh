#!/usr/bin/env bash
# CopilotKit frontend on :3000. Run from the repo root, in a second terminal.
set -euo pipefail

# Ensure nvm and Linux node/npm are loaded in non-interactive subshells
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
if [ -s "$NVM_DIR/nvm.sh" ]; then
    . "$NVM_DIR/nvm.sh"
fi

cd "$(dirname "$0")/frontend"
if [ ! -d "node_modules" ]; then
    npm install
fi
exec npm run dev
