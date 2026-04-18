# Re-export API dependencies from canonical package
import sys
from apps.api.app.api.dependencies import *  # noqa: F401

# Make apps.api.app.api.dependencies and app.api.dependencies refer to the same
# module object so tests that monkeypatch app.api.dependencies affect the
# canonical module used by the application.
sys.modules.setdefault('app.api.dependencies', sys.modules[__name__])
sys.modules.setdefault('apps.api.app.api.dependencies', sys.modules[__name__])
