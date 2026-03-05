# hospitable-ops (skeleton)

Minimal skeleton for the Hospitable Ops backend. Use `dev-setup.sh` to prepare a local venv and install minimal dependencies.

Quickstart

1. Prepare dev environment:
   - cd hospitable-ops
   - ./dev-setup.sh

2. Run migrations (sqlite dev by default):
   - alembic upgrade head

3. Seed demo data (optional):
   - python -c "from app.services.rbac_service import init_db; init_db()"

4. Start server:
   - . .venv/bin/activate && uvicorn app.main:app --reload

Notes
- Default DATABASE_URL is sqlite:///./hospitable_ops_dev.db; change in db/session.py for Postgres.
- See /scripts for sample backfill scripts.
