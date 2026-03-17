# Architecture

## Target shape
Use a modular monorepo layout that keeps platform primitives distinct from domain packs.

## Recommended top-level layout
```text
apps/
  api/
  web/
packages/
  contracts/
  domain/
  shared/
docs/
scripts/
tests/
```

## Backend architecture
Recommended backend layers:
- API routers
- schemas
- services
- models
- permissions
- audit/events
- db/core

Route handlers should stay thin.
Business logic belongs in service-layer code.

## Frontend architecture
Pages are shells.
Widgets do the work.
