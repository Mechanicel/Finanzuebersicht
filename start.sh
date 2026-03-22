#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

echo "[finanzuebersicht] Starte Launcher..."

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "[finanzuebersicht] FEHLER: .venv fehlt. Bitte einmalig ausführen: uv venv .venv && uv sync"
  exit 2
fi

exec "$VENV_PYTHON" -m FrontendService.src.launcher
