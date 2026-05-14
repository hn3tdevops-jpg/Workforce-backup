# Alembic migration plan — model consolidation (2026-04-20)

Goal
- Safely migrate application schema from local model implementations to canonical packages.workforce models with minimal downtime and reversible steps.

Assumptions
- Canonical models in packages.workforce are the target schema.
- Tests have been run with SKIP_WORKFORCE_MODELS toggles; DB uses SQLite for tests and possibly Postgres in prod.

Risks & considerations
- Column type differences (UUID vs string) require careful migration and adapter checks.
- Constraint and index renames may fail on SQLite; use batch_alter_table for non-destructive changes.
- Avoid dropping legacy tables until data has been migrated and verified.

Checklist
1. Inventory canonical vs local schemas (tables, columns, types, constraints).
2. For each difference, create a migration plan: add new column (nullable), backfill data, switch application to write both columns (if needed), verify, then drop legacy column in a follow-up revision.
3. Prefer additive, non-destructive migrations when possible.
4. Use `with op.batch_alter_table(...)` for SQLite migrations that change constraints or types.
5. Run tests and a staging DB restore from production snapshot to validate migration.
6. Schedule a maintenance window for prod schema changes that are not online-safe.

Commands & workflow
- Generate a draft migration: `alembic revision -m "consolidate models: adopt packages.workforce" --autogenerate` (review carefully; manual edits likely needed)
- For SQLite-safe changes, use batch_alter_table: see Alembic docs.
- Run local test DB: `pytest -q` after applying migration to test harness.
- Deploy migration to staging, run smoke tests, then prod.

Post-migration cleanup
- Remove *_local modules and compatibility shims in a follow-up commit once migrations and verification pass.
- Remove transient __table_args__ extend_existing markers (already done).
- Update docs/DECISIONS.md and CHANGELOG with final decision and migration notes.

Notes
- This file is a checklist and guidance. Create concrete alembic revision files (one per logical change) rather than a single large migration when possible.
