#!/usr/bin/env bash
# regenerate_docs_index.sh
# Generate a simple JSON index of markdown documents in docs/ and repository root (top-level .md)

set -euo pipefail
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

python3 - <<'PY'
import os, json, re
root = os.getcwd()

def gather():
    md_files = []
    docs_dir = os.path.join(root, 'docs')
    if os.path.isdir(docs_dir):
        for dirpath, dirs, files in os.walk(docs_dir):
            for f in files:
                if f.endswith('.md'):
                    md_files.append(os.path.relpath(os.path.join(dirpath, f), root))
    # include top-level markdown files in the repo root
    for f in os.listdir(root):
        if f.endswith('.md') and os.path.isfile(os.path.join(root, f)):
            md_files.append(f)
    return sorted(set(md_files))

items = []
for p in gather():
    title = None
    full = os.path.join(root, p)
    try:
        with open(full, 'r', encoding='utf-8') as fh:
            for line in fh:
                line = line.strip()
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
                if line.startswith('## '):
                    title = line[3:].strip()
                    break
    except Exception:
        title = None
    if not title:
        title = os.path.basename(p)
    mtime = int(os.path.getmtime(full)) if os.path.exists(full) else None
    items.append({'path': p, 'title': title, 'mtime': mtime})

# Ensure docs dir exists and write index
docs_out_dir = os.path.join(root, 'docs')
os.makedirs(docs_out_dir, exist_ok=True)
with open(os.path.join(docs_out_dir, 'docs_index.json'), 'w', encoding='utf-8') as fh:
    json.dump(items, fh, indent=2, ensure_ascii=False)
# Also write a root-level copy for legacy consumers
with open(os.path.join(root, 'PROJECT_DOCS_INDEX.json'), 'w', encoding='utf-8') as fh:
    json.dump(items, fh, indent=2, ensure_ascii=False)
print(f"Wrote {len(items)} markdown entries")
PY
