#!/usr/bin/env bash
# setup.sh — First-time setup for the Presenton Electron desktop app.
#
# Run this once after cloning the repository:
#   cd electron && bash scripts/setup.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ELECTRON_DIR="${ROOT_DIR}/electron"
FRONTEND_DIR="${ROOT_DIR}/frontend"

echo "=== Presenton Desktop — First-time setup ==="
echo "Project root: ${ROOT_DIR}"

# ─── Node dependencies ────────────────────────────────────────────────────────

echo ""
echo "--- Installing Electron Node dependencies ---"
cd "${ELECTRON_DIR}"
npm install

echo ""
echo "--- Installing Next.js frontend dependencies ---"
cd "${FRONTEND_DIR}"
npm install

# ─── Python dependencies ──────────────────────────────────────────────────────

echo ""
echo "--- Installing Python dependencies (uv) ---"
cd "${ROOT_DIR}"

if command -v uv &>/dev/null; then
  uv sync --all-extras
else
  echo "  'uv' not found — falling back to pip."
  python3 -m pip install -e ".[dev]"
fi

# ─── Verify Python imports ────────────────────────────────────────────────────

echo ""
echo "--- Verifying shared kernel imports ---"
python3 - <<'PYEOF'
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))
from shared.infrastructure.in_memory_event_bus import InMemoryEventBus
from shared.infrastructure.database import DatabaseConfig, create_engine_from_config
print("  OK: shared kernel imports resolved.")
PYEOF

# ─── Done ─────────────────────────────────────────────────────────────────────

echo ""
echo "=== Setup complete! ==="
echo ""
echo "To start the app in development mode:"
echo "  cd electron && npm run dev"
echo ""
