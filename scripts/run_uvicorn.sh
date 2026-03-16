#!/usr/bin/env bash
set -euo pipefail

# Script to run the FastAPI app with uvicorn for iterative development
# Usage: ./scripts/run_uvicorn.sh

exec uvicorn apps.api.app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --reload
