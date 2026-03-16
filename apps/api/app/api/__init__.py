# Expose additional API modules (routes, deps) from the workforce package if present
import os
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

# Compute repository root (projects_active) reliably by ascending four levels from this file
_repo_root = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
_workforce_api = os.path.normpath(os.path.join(_repo_root, 'packages', 'workforce', 'workforce', 'app', 'api'))
if os.path.isdir(_workforce_api) and _workforce_api not in __path__:
    __path__.insert(0, _workforce_api)
