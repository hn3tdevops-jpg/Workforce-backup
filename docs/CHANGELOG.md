# Changelog

## 2026-04-27
### Added
- Centralized import guard and diagnostics to stabilize tests (SKIP_WORKFORCE_MODELS).
- Admin invite endpoint and admin-create-with-membership seeding: creates Memberships (invited/active) and owner role assignment when requested.

### Fixed
- Clarified behavior: public /auth/register creates a user account but does not create a workspace/membership; admin invite/create flows seed memberships.

## 2026-04-24
### Fixed
- Applied code formatting and import sorting (black, isort) and removed unused imports (autoflake). Updated .flake8 to reduce false-positives; fixed small test issues and import placement.
- Ran full test suite: 49 passed.

## 2026-04-13
### Changed
- Permission dependencies now support optional location-scoped checks. Endpoints accept optional `location_id` query param which is forwarded to permission resolver.

## 2026-03-16
### Added
- repo operating system docs
- Copilot repo instructions
- backend and frontend instruction files
- PR template
- recovery playbook
- domain model and architecture docs
- checkpoint helper script
