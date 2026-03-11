# Workforce / Hospitable Repo Cleanup Instructions

## Objective
Refactor and clean the repository into a clear monorepo structure for hospitality operations, without deleting working business logic.

## Primary goals
1. Remove clutter from repo root.
2. Separate runtime artifacts from source code.
3. Standardize Python backend layout.
4. Isolate frontend/web code from backend code.
5. Preserve all existing logic, configs, tests, and docs.
6. Make the repo easier to run, test, and extend.

## Required end-state structure

projects_active/
├── apps/
│   ├── api/              # FastAPI backend
│   ├── web/              # frontend / Next.js / React if present
│   └── ops/              # optional operations-specific app if needed
├── packages/
│   ├── workforce/        # workforce domain package
│   ├── hospitable/       # hospitable integration package
│   └── rbac/             # shared RBAC package if appropriate
├── docs/
│   ├── architecture/
│   ├── rbac/
│   └── plans/
├── scripts/
├── tests/
├── alembic/
├── pyproject.toml
├── README.md
└── .gitignore

## Mandatory rules
- Do NOT delete business logic unless it is clearly duplicate generated junk.
- Do NOT delete tests unless they are obviously broken duplicates and replaced with equivalent tests.
- Do NOT delete docs; move and organize them.
- Do NOT commit runtime artifacts.
- Do NOT keep virtualenvs, sqlite db files, egg-info, logs, __pycache__, or node_modules in tracked source layout.
- Keep imports working; update imports after moving files.
- Update pyproject.toml to reflect the new package layout.
- Preserve alembic and database migration functionality.
- Preserve FastAPI entrypoint and ensure there is one canonical app entrypoint.

## Cleanup tasks

### A. Runtime artifact cleanup
Identify and remove from tracked source structure:
- venv/
- .venv/
- *.egg-info/
- __pycache__/
- .pytest_cache/
- .mypy_cache/
- .ruff_cache/
- *.log
- *.db
- node_modules/
- .next/
- dist/
- build/

Update .gitignore to include all of the above.

### B. Root directory cleanup
Move documentation files into:
- docs/plans/
- docs/rbac/
- docs/architecture/

Examples:
- HN3T_MASTER_PLAN.md -> docs/plans/
- MASTER_PLAN.md -> docs/plans/
- RBAC_AUDIT_INDEX.md -> docs/rbac/
- RBAC_CODE_SNIPPETS.md -> docs/rbac/
- RBAC_IMPLEMENTATION_AUDIT.md -> docs/rbac/
- RBAC_SUMMARY.txt -> docs/rbac/

### C. Backend normalization
If `app/` is the real FastAPI application, keep it as the canonical backend app under:
- apps/api/app/

If `workforce/` contains domain code, move it to:
- packages/workforce/

If `hospitable/` contains integration logic, move it to:
- packages/hospitable/

If `hospitable-ops/` is backend logic, merge carefully into:
- apps/api/ or packages/hospitable/
depending on whether it is app-specific or reusable domain/integration logic.

If `hospitable-web/` is frontend code, move it to:
- apps/web/

### D. Python packaging
Update `pyproject.toml` so editable install works with:
- apps/api
- packages/workforce
- packages/hospitable
- packages/rbac (if created)

Ensure import paths are consistent and valid after refactor.

### E. FastAPI structure
Target backend structure:

apps/api/
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── integrations/
│   └── main.py

Move code into this structure where appropriate.

### F. Tests
Keep tests under root `tests/` unless there is a strong reason to colocate.
Fix imports after refactor.

### G. Deliverables
After refactor, produce:
1. Updated repo tree summary in `docs/architecture/REPO_STRUCTURE.md`
2. Updated `.gitignore`
3. Updated `pyproject.toml`
4. Updated `README.md` with run instructions
5. A migration summary in `docs/architecture/REFACTOR_NOTES.md`

## Required validation
Before finishing, run:
- python -m pytest
- ruff check .
- python -m compileall apps packages

If commands fail, fix straightforward import/path issues and summarize any remaining blockers.

## Safety constraints
- Prefer moving files over rewriting logic.
- Prefer minimal invasive changes.
- Preserve existing behavior first; improve architecture second.
- If there is ambiguity, choose the least destructive refactor.