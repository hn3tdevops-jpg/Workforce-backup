#!/usr/bin/env bash
set -e
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn

echo "Dev setup complete. Run: . .venv/bin/activate && uvicorn app.main:app --reload"