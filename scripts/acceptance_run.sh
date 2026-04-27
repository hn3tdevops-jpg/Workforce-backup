#!/usr/bin/env bash
set -euo pipefail

# Simple acceptance test runner using docker-compose
# Usage: ./scripts/acceptance_run.sh

DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$DIR"

# Bring up test services (expects docker-compose.yml in repo root)
docker-compose up -d --build db

# Wait for Postgres
echo "Waiting for Postgres..."
until docker-compose exec -T db pg_isready -U postgres >/dev/null 2>&1; do
  sleep 1
done

echo "Running migrations"
# Adjust DATABASE_URL if your docker-compose uses a different host
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/workforce_test
alembic upgrade head

echo "Running pytest acceptance tests"
pytest -q tests/test_users_endpoints.py -q -s || TEST_STATUS=$?

# Capture exit status
if [ -z "${TEST_STATUS+x}" ]; then
  TEST_STATUS=0
fi

echo "Tearing down docker-compose"
docker-compose down

exit $TEST_STATUS
