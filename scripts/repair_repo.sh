#!/usr/bin/env bash
set -euo pipefail

cd ~/projects_active

echo "==> Detecting Python files"
PYFILES=$(find apps packages -type f -name "*.py" 2>/dev/null || true)

echo "==> Repairing imports"

for f in $PYFILES
do
    sed -i 's/from app\./from apps.api.app./g' "$f" || true
    sed -i 's/import app\./import apps.api.app./g' "$f" || true

    sed -i 's/from workforce\./from packages.workforce./g' "$f" || true
    sed -i 's/import workforce\./import packages.workforce./g' "$f" || true

    sed -i 's/from hospitable\./from packages.hospitable./g' "$f" || true
    sed -i 's/import hospitable\./import packages.hospitable./g' "$f" || true
done

echo "==> Ensuring Python packages exist"

touch apps/__init__.py
touch apps/api/__init__.py
touch apps/api/app/__init__.py

touch packages/__init__.py
touch packages/workforce/__init__.py
touch packages/hospitable/__init__.py

echo "==> Updating pyproject package discovery"

if ! grep -q "packages.find" pyproject.toml; then
cat >> pyproject.toml <<EOF

[tool.setuptools.packages.find]
where = ["apps", "packages"]
EOF
fi

echo "==> Cleaning compiled artifacts"

find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

echo "==> Running quick validation"

python -m compileall apps packages || true

echo
echo "Repo repair complete."
echo
echo "Next run:"
echo "pytest"
echo "ruff check ."