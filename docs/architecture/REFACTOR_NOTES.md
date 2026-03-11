# Refactor Notes

This cleanup script:
- moved planning docs into docs/plans
- moved RBAC docs into docs/rbac
- moved app into apps/api when present
- moved workforce into packages/workforce when present
- moved hospitable into packages/hospitable when present
- moved hospitable-ops into apps/ops when present
- moved hospitable-web into apps/web when present
- removed common runtime artifacts from the working tree
- updated .gitignore

Manual follow-up still required:
- repair Python imports after moves
- update pyproject.toml package paths
- validate alembic config
- run tests and fix import/path issues
