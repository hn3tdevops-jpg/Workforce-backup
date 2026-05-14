# Expose modules from hospitable-ops/app as part of this 'app' package so tests importing app.services.* succeed.
import os

# Keep this package as a regular package with a stable import path.
# Avoid using pkgutil.extend_path to prevent namespace package merging with
# packages/workforce which can cause duplicate model registration and
# surprising import resolution.

_repo_root = os.path.dirname(os.path.dirname(__file__))

# Prefer hospitable-ops app for local overrides is handled elsewhere; do not modify __path__ here.
