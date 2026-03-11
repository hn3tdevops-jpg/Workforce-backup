# GitHub Copilot instructions for the Workforce repository

This document provides concise, repository-specific guidance for Copilot CLI sessions working in this project.

Working directory
- Run developer and CI commands from the workforce/ project root (the directory containing pyproject.toml and README.md). Example: `cd scheduler/workforce`.
- Activate the virtualenv before running project commands (venv is the local convention used in README).

Build, test, and lint commands
- Install (development): `pip install -e .` (run from workforce/ with venv active).
- Run dev server: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- Database migrations: `alembic upgrade head` (or `python -m app.cli.main init-db`).
- Seed demo data: `python -m app.cli.main seed-demo`.
- Run full test suite: `pytest -q`.
- Run a single test file: `pytest tests/test_matching.py -q`.
- Run tests by keyword: `pytest -k <substring> -q`.
- Lint: `ruff check .` and auto-fix: `ruff check --fix .` (dev extras in pyproject).

Quick CLI references
- `python -m app.cli.main init-db` — run migrations / initialize DB
- `python -m app.cli.main seed-demo` — create demo dataset (prints sample IDs)
- `python -m app.cli.main match --shift-id <UUID>` — print ranked candidates for a shift
- `python -m app.cli.main purge` — maintenance: purge expired messages and stale refresh tokens

High-level architecture
- Stack: FastAPI (ASGI) + SQLAlchemy 2 (ORM) + Alembic + Pydantic v2 + Jinja2; deployed using a2wsgi for PythonAnywhere WSGI setups.
- Layering and locations:
  - app/models/ — SQLAlchemy ORM model classes (source of truth for schema)
  - app/schemas/ — Pydantic request/response models (separate from ORM models)
  - app/services/ — domain/business logic (matching, audit, etc.)
  - app/api/routes/ — FastAPI routers organized by domain
  - app/cli/ — CLI entrypoints (migration helpers, seeders, background tasks)
  - app/core/ — configuration, DB engine/session factory, logging helpers
- Multi-tenancy: Employees are global; tenant scoping for queries is enforced by joining through the Employment table and filtering on business_id.
- Audit: Mutating operations write AuditLog rows; see the README and code for log_change(...) usage.
- Matching: Candidate selection requires (1) active Employment in the shift's business, (2) matching EmployeeRole, (3) an AvailabilityBlock fully covering the shift window with status preferred/available, and (4) no overlapping offered/assigned/checked_in assignment; results are sorted preferred→available, proficiency DESC, last_name ASC.

Key conventions and patterns (repository-specific)
- Model mixins: Most models use `UUIDMixin` and `TimestampMixin` (id, created_at, updated_at) — these are repo-wide conventions.
- Route mutation pattern: `db.add(obj)` → `db.flush()` → `log_change(...)` → `db.commit()` → `db.refresh(obj)`. Always flush before logging so generated IDs exist.
- Session usage: Routes use `db: Session = Depends(get_session)`; CLI scripts use `db_session()` context manager that auto-commits on exit and rolls back on exceptions.
- Alembic: Import application models in `app.models.__init__` so Alembic's env.py registers metadata; `render_as_batch=True` is configured for SQLite compatibility.
- Tests: Tests set `DATABASE_URL` (often `sqlite://`) before importing app modules and use an in-memory SQLite engine; ensure imports register models (`import app.models`).
- Pydantic read models: read/response schemas use `model_config = {"from_attributes": True}` to allow from-ORM conversion.
- CLI and background jobs: Use `python -m app.cli.main <command>` for repository-provided management tasks; these expect to be run from the project root with a proper env (see README `.env` usage).

Files and locations to check when answering repo questions
- app/models/ — schema details and mixins
- app/services/matching.py — canonical matching/business rules
- app/cli/ — CLI helpers and scripts used for seeds and maintenance
- alembic/ and alembic.ini — migrations and env configuration
- README.md and pyproject.toml — canonical commands, dependencies, and dev extras

AI assistant config files
- No repository-specific assistant configs were found (CLAUDE.md, AGENTS.md, .cursorrules, .windsurfrules, CONVENTIONS.md, AIDER_CONVENTIONS.md, .clinerules) at scan time. If such files are added later, include their important rules here.

Notes for Copilot sessions
- Use the project root (workforce/) for commands and virtualenv activation.
- When making code edits, prefer minimal surgical changes and run relevant tests (or the single test) to validate behavior.
- When changing database models, ensure Alembic migrations are generated and `app.models` is imported so metadata is visible to Alembic.


