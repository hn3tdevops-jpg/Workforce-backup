# Re-export API dependencies from canonical package
import sys
import importlib

# Import canonical module and rebind module names so both import paths refer
# to the same module object. This ensures monkeypatching either name affects
# the single canonical module used at runtime.
canonical = importlib.import_module("apps.api.app.api.dependencies")
# Override any existing entries so both keys point to the canonical module
sys.modules['apps.api.app.api.dependencies'] = canonical
sys.modules['app.api.dependencies'] = canonical

# Expose the canonical module's public names for compatibility
from apps.api.app.api.dependencies import *  # noqa: F401,F403,E402
