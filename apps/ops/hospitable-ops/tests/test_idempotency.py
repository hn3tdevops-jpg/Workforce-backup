from apps.api.app.services.idempotency import init_idempotency_db, create_key_if_missing, get_by_key, store_response


def setup_module(module):
    init_idempotency_db()


def test_idempotency_key_lifecycle():
    key = 'test-key-1'
    ik = create_key_if_missing(key, location_id='loc-1', request_hash='abc')
    assert ik.key == key
    stored = store_response(key, 200, {'ok': True})
    assert stored.response_status == 200
    fetched = get_by_key(key)
    assert fetched.response_status == 200
