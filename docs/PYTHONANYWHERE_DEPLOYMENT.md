PythonAnywhere deployment notes

Working directory: /home/hn3t/projects_active
Virtualenv: /home/hn3t/.virtualenvs/workforce-api (ensure Web tab points to this)
WSGI file path (PythonAnywhere): /var/www/hn3t_pythonanywhere_com_wsgi.py
Project WSGI entrypoint (repo): /home/hn3t/projects_active/wsgi.py

Recommended WSGI delegate (ensure the /var/www file imports the project wsgi):
    from importlib import import_module
    w = import_module('wsgi')
    application = getattr(w, 'application')

Reload step: Touch the active WSGI file or click Reload in the PythonAnywhere Web UI.

Validation commands (run from repo root):
    python scripts/check_canonical_imports.py
    PYTHONPATH=apps/api:. alembic current
    PYTHONPATH=apps/api:. alembic upgrade head
    PYTHONPATH=apps/api:. pytest -q tests

Live health checks:
    curl -i https://hn3t.pythonanywhere.com/
    curl -i https://hn3t.pythonanywhere.com/health
    curl -i https://hn3t.pythonanywhere.com/api/v1/health/
