# Changelog

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
