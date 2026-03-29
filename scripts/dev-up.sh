#!/usr/bin/env bash
set -euo pipefail

SERVICE="${1:-api-gateway}"
PORT="${2:-8000}"

cd "$(dirname "$0")/../services/${SERVICE}"
uv sync
uv run uvicorn app.main:app --reload --port "${PORT}"
