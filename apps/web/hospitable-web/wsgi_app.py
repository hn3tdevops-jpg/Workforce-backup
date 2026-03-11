from flask import Flask, send_from_directory, abort
import os

# Serve built frontend from frontend/dist
static_dir = os.path.join(os.path.dirname(__file__), "frontend", "dist")
app = Flask(__name__, static_folder=static_dir, static_url_path="")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # If the requested asset exists in dist, serve it; otherwise return index.html (SPA behavior)
    target = os.path.join(app.static_folder, path)
    if path and os.path.exists(target) and os.path.isfile(target):
        return send_from_directory(app.static_folder, path)
    index_path = os.path.join(app.static_folder, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(app.static_folder, 'index.html')
    # If dist isn't present yet, show a helpful message
    abort(404, description='Frontend not built. Run `npm run build` in hospitable-web/frontend.')
