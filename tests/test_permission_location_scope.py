import uuid

import pytest

from app.api.dependencies import require_permission_with_location, AuthContext
import app.services.rbac_service as rbac_service


class DummySession:
    async def run_sync(self, func):
        return func("sync_session_dummy")


@pytest.mark.asyncio
async def test_require_permission_forwards_location(monkeypatch):
    captured = {}

    def fake_user_has_permission(session, user_id, permission_code, business_id, location_id):
        captured['args'] = (session, user_id, permission_code, business_id, location_id)
        return True

    import app.api.dependencies as deps
    monkeypatch.setattr(deps, "user_has_permission", fake_user_has_permission)

    auth = AuthContext(user=None, user_id=uuid.UUID(int=1), business_id=uuid.UUID(int=2), claims={})
    session = DummySession()
    expected_loc = uuid.UUID(int=3)

    dep = require_permission_with_location("test.perm", location_resolver=lambda: None)
    result_auth = await dep(auth=auth, session=session, location_id=expected_loc)
    assert result_auth is auth
    assert captured['args'][4] == expected_loc
