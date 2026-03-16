# Expose core helpers from the workforce package when available
import os
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

_repo_root = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
_workforce_core = os.path.normpath(os.path.join(_repo_root, 'packages', 'workforce', 'workforce', 'app', 'core'))
if os.path.isdir(_workforce_core) and _workforce_core not in __path__:
    __path__.insert(0, _workforce_core)
