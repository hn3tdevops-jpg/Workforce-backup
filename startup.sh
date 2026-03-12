#!/bin/bash
set -e

export PYTHONPATH=apps/api

echo "==> Running database migrations..."
python -m alembic upgrade head

echo "==> Running idempotent seed..."
python -m apps.api.app.modules.hospitable.seeds.silver_sands_seed_prod

echo "==> Starting API server on port ${PORT:-8000}..."
exec uvicorn apps.api.app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
