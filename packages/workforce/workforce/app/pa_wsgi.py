# Minimal WSGI app for PythonAnywhere: serves the static index.html for the workforce UI.
# Usage on PythonAnywhere:
# - Create a web app (manual via dashboard)
# - Set "Source code" to /home/hn3t/projects_active/packages/workforce/workforce/app
# - Point WSGI configuration to this file (pa_wsgi.app)
# - Install requirements: pip install Flask (or include in virtualenv)

from flask import Flask, send_file, abort
import os

app = Flask(__name__)

# Absolute path to the index file confirmed by the user
INDEX_PATH = '/home/hn3t/projects_active/packages/workforce/workforce/app/templates/index.html'

@app.route('/')
def index():
    if os.path.exists(INDEX_PATH):
        return send_file(INDEX_PATH)
    abort(404)

# Optionally serve other static files under the templates directory (CSS/JS assets)
@app.route('/<path:subpath>')
def catch_all(subpath):
    # Prevent path traversal
    base = os.path.dirname(INDEX_PATH)
    candidate = os.path.normpath(os.path.join(base, subpath))
    if not candidate.startswith(base):
        abort(403)
    if os.path.exists(candidate) and os.path.isfile(candidate):
        return send_file(candidate)
    abort(404)

# WSGI entrypoint name expected by PythonAnywhere
def app_factory():
    return app

# Expose `app` for WSGI
app = app
