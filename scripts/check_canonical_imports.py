#!/usr/bin/env python3
import sys, os
PROJECT_ROOT = os.path.abspath(os.getcwd())
API_ROOT = os.path.join(PROJECT_ROOT, 'apps', 'api')
for path in [API_ROOT, PROJECT_ROOT]:
    if path in sys.path:
        sys.path.remove(path)
    sys.path.insert(0, path)
try:
    import app.db.base as dbbase
    f = os.path.abspath(dbbase.__file__)
    print('app.db.base.__file__ =', f)
    print('Has Base:', hasattr(dbbase, 'Base'))
    if os.path.normpath(os.path.join(PROJECT_ROOT, 'apps', 'api')) not in os.path.normpath(f):
        print('ERROR: app.db.base did not resolve under apps/api', file=sys.stderr)
        sys.exit(2)
except Exception as e:
    print('ERROR importing app.db.base:', e, file=sys.stderr)
    sys.exit(1)
