# Phase Status

## Current phase
Phase 0 — Foundation Freeze

## Objective
Stabilize the repository structure, planning system, and restore process before more feature work.

## Exit criteria
- repo-base files are committed
- app still boots
- runtime target documented
- first checkpoint tag created
- next phase queued as tenant/RBAC core

## Current checkpoint
- The app import path now defaults to the safe local model surface via `SKIP_WORKFORCE_MODELS=1` in the entrypoints.
- Health, bootstrap, and route-protection tests are passing locally.
- Next step: validate the full suite and then confirm the deployment entrypoint picks up the updated boot path.
