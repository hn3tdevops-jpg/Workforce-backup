#!/usr/bin/env bash
set -euo pipefail

cd ~/projects_active

echo "==> Creating target directories"
mkdir -p apps/api apps/web apps/ops
mkdir -p packages/workforce packages/hospitable packages/rbac
mkdir -p docs/architecture docs/plans docs/rbac
mkdir -p scripts

echo "==> Moving docs"
mv HN3T_MASTER_PLAN.md docs/plans/ 2>/dev/null || true
mv MASTER_PLAN.md docs/plans/ 2>/dev/null || true
mv RBAC_AUDIT_INDEX.md docs/rbac/ 2>/dev/null || true
mv RBAC_CODE_SNIPPETS.md docs/rbac/ 2>/dev/null || true
mv RBAC_IMPLEMENTATION_AUDIT.md docs/rbac/ 2>/dev/null || true
mv RBAC_SUMMARY.txt docs/rbac/ 2>/dev/null || true

echo "==> Moving major code directories if present"
if [ -d app ] && [ ! -d apps/api/app ]; then
  mkdir -p apps/api
  mv app apps/api/
fi

if [ -d workforce ] && [ ! -d packages/workforce/workforce ]; then
  mkdir -p packages/workforce
  mv workforce packages/workforce/
fi

if [ -d hospitable ] && [ ! -d packages/hospitable/hospitable ]; then
  mkdir -p packages/hospitable
  mv hospitable packages/hospitable/
fi

if [ -d hospitable-ops ] && [ ! -d apps/ops/hospitable-ops ]; then
  mkdir -p apps/ops
  mv hospitable-ops apps/ops/
fi

if [ -d hospitable-web ] && [ ! -d apps/web/hospitable-web ]; then
  mkdir -p apps/web
  mv hospitable-web apps/web/
fi

echo "==> Removing runtime junk from working tree"
rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache .next dist build node_modules 2>/dev/null || true
find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.egg-info" -prune -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.log" -delete 2>/dev/null || true
find . -type f -name "*.db" -delete 2>/dev/null || true

echo "==> Rebuilding .gitignore entries"
touch .gitignore

append_if_missing() {
  grep -qxF "$1" .gitignore || echo "$1" >> .gitignore
}

append_if_missing ""
append_if_missing "# Python"
append_if_missing "venv/"
append_if_missing ".venv/"
append_if_missing "__pycache__/"
append_if_missing ".pytest_cache/"
append_if_missing ".mypy_cache/"
append_if_missing ".ruff_cache/"
append_if_missing "*.egg-info/"
append_if_missing "*.pyc"
append_if_missing "*.pyo"
append_if_missing ""
append_if_missing "# Runtime artifacts"
append_if_missing "*.log"
append_if_missing "*.db"
append_if_missing ""
append_if_missing "# Node"
append_if_missing "node_modules/"
append_if_missing ".next/"
append_if_missing "dist/"
append_if_missing "build/"

echo "==> Writing repo structure note"
cat > docs/architecture/REPO_STRUCTURE.md <<'EOF'
# Repo Structure

## Target layout
- apps/api -> FastAPI application
- apps/web -> frontend application
- apps/ops -> operations-specific app code
- packages/workforce -> workforce domain package
- packages/hospitable -> hospitable integration package
- packages/rbac -> shared RBAC package
- docs/plans -> planning docs
- docs/rbac -> RBAC docs
- docs/architecture -> architecture notes
EOF

echo "==> Writing refactor notes"
cat > docs/architecture/REFACTOR_NOTES.md <<'EOF'
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
EOF

echo "==> Cleanup complete"
echo
echo "Next steps:"
echo "1. git status"
echo "2. update pyproject.toml"
echo "3. run pytest"
echo "4. repair imports as needed"