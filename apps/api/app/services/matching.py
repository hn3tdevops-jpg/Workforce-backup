# Compatibility shim: expose find_candidates_for_shift under apps.api.app.services.matching
# by importing the implementation from the workforce package implementation file.
import importlib.util
import os

_target = '/home/hn3t/projects_active/packages/workforce/workforce/app/services/matching.py'
if os.path.isfile(_target):
    spec = importlib.util.spec_from_file_location('workforce_matching', _target)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Re-export symbol used by tests
    find_candidates_for_shift = getattr(module, 'find_candidates_for_shift')
else:
    raise ImportError(f"Workforce matching implementation not found at {_target}")

__all__ = ['find_candidates_for_shift']
