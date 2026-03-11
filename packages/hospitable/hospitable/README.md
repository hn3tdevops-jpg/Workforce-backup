Hospitable — Minimal UI

Files created in /home/hn3t/hospitable:
- app.py       (Flask app serving static/index.html)
- wsgi.py      (WSGI entrypoint: from app import app as application)
- static/index.html

To configure on PythonAnywhere:
1. Create or edit the web app at hospitable-hn3t.pythonanywhere.com in the PythonAnywhere dashboard.
2. Set the "WSGI configuration file" to point to /home/hn3t/hospitable/wsgi.py (or import it from your existing WSGI file).
3. Ensure Flask is available in the web app's virtualenv (pip install flask).
4. Reload the web app.

Reference: HN3T_MASTER_PLAN.md in the home directory contains project details to expand the UI.
