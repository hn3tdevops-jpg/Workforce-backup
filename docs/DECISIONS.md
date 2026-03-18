# Decisions

## D-0001 Recoverability-first repo operating system
Date: 2026-03-16
Status: accepted

Decision:
- The repository must maintain a recoverability-first operating system.
- Planning, change tracking, work logging, and restore checkpoints are first-class project assets.
- Structural work must update the project docs, not just the code.

Rationale:
The project is expanding across multiple domains and needs a built-in method for tracking changes, decisions, and safe restore points.

## D-0002 Workforce as platform core first
Date: 2026-03-16
Status: accepted

Decision:
- Workforce is a platform core before it is a domain-specific app.
- Shared primitives must support hospitality, housekeeping, maintenance, field service, and similar service operations.
- Domain-specific workflows are extensions built on top of shared platform capabilities.

Rationale:
The same backend primitives should support multiple service-operation domains without duplicating the core system.

## D-0003 Widget-first workspaces for the UI
Date: 2026-03-16
Status: accepted

Decision:
- The interface will use widget-first workspaces rather than rigid page-first design.
- Pages act as shells and layout containers.
- Functional UI units should be modular widgets that can be arranged, shown, hidden, and permission-scoped.

Rationale:
Rigid page-first design makes cross-domain customization harder and duplicates UI patterns.

## D-0004 Canonical runtime surfaces
Date: 2026-03-16
Status: accepted

Decision:
- `apps/api` is the canonical backend runtime surface.
- `apps/web/hospitable-web` is the canonical frontend runtime surface.
- `apps/ops/*` contains domain-specific operational modules.
- `packages/contracts` and `packages/domain` are shared-library space only.
- Root `alembic/` is the canonical migration surface.
- `packages/workforce/workforce` and `packages/hospitable/hospitable` are frozen legacy surfaces pending extraction or archive.

Rationale:
The repository contains multiple overlapping app roots, migrations, databases, and deployment surfaces. Freezing one canonical execution path simplifies recovery, deployment, and future refactors.

## D-0005 Local-only artifacts are never tracked
Date: 2026-03-16
Status: accepted

Decision:
- `.env*` files are local-only unless they are explicit examples like `.env.example`.
- Local databases and database backups are never tracked.
- Frontend local env files like `.env.local` are never tracked.

Rationale:
These files create security risk, pollute history, and make recovery harder because local machine state leaks into the repo.

## D-0006 Canonical backend import root and migration surface
Date: 2026-03-16
Status: accepted

Decision:
- The canonical backend Python package root is `app`.
- The canonical backend source directory is `apps/api/app`.
- The canonical ASGI entrypoint is `app.main:app`.
- The canonical Alembic migration surface is the repository root `alembic/`.

Rationale:
Root packaging, runtime imports, and Alembic must agree on one import path and one metadata source. Mixed import roots (`apps.api.app` vs `app`) will eventually cause broken migrations, runtime import failures, and deployment drift.

## D-0008 Canonical backend contract must pass from repo root
Date: 2026-03-16
Status: accepted

Decision:
- Backend validation is performed from the repository root.
- Canonical checks use `PYTHONPATH=apps/api`.
- Canonical backend tests run with `pytest -q tests`.

Rationale:
This prevents accidental imports from legacy app roots and stops pytest from collecting unrelated projects on the machine.