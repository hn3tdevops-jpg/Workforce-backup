# Expose modules from hospitable-ops/app as part of this 'app' package so tests importing app.services.* succeed.
import os
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

_repo_root = os.path.dirname(os.path.dirname(__file__))
_extra = os.path.join(_repo_root, 'hospitable-ops', 'app')
if os.path.isdir(_extra) and _extra not in __path__:
    __path__.insert(0, _extra)
