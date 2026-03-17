#!/usr/bin/env bash
set -euo pipefail

TAG_NAME="${1:-}"
if [[ -z "$TAG_NAME" ]]; then
  echo "Usage: scripts/checkpoint.sh <tag-name>"
  exit 1
fi

git status --short
echo
echo "Creating annotated checkpoint tag: $TAG_NAME"
git tag -a "$TAG_NAME" -m "Checkpoint: $TAG_NAME"
echo "Created tag $TAG_NAME"
echo "Push with: git push origin $TAG_NAME"
