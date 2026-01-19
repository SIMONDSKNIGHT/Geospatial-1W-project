
def test_health_ok(client, app_module):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
    queries = app_module._test_dummy_cursor.queries
    assert len(queries) == 1
    sql, params = queries[0]
    assert "SELECT 1" in sql
    assert params is None
