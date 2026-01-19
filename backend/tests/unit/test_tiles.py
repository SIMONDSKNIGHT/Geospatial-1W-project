def test_tile_returns_pbf_and_cache_headers(client, app_module):
    # First request should MISS and populate cache
    r1 = client.get("/tiles/1/2/3.pbf")
    assert r1.status_code == 200
    assert r1.headers.get("content-type", "").startswith("application/x-protobuf")
    assert r1.headers.get("X-Cache") == "MISS"
    assert "Cache-Control" in r1.headers
    assert r1.content == b"dummy_mvt"

    # Second identical request should HIT
    r2 = client.get("/tiles/1/2/3.pbf")
    assert r2.status_code == 200
    assert r2.headers.get("X-Cache") == "HIT"
    assert r2.content == b"dummy_mvt"


def test_tile_cache_key_includes_mode(client, app_module):
    # cluster (default) -> MISS
    r1 = client.get("/tiles/1/2/3.pbf")
    assert r1.headers.get("X-Cache") == "MISS"

    # different mode should be treated as different cache key -> MISS again
    r2 = client.get("/tiles/1/2/3.pbf?mode=raw")
    assert r2.headers.get("X-Cache") == "MISS"

    # same mode again -> HIT
    r3 = client.get("/tiles/1/2/3.pbf?mode=raw")
    assert r3.headers.get("X-Cache") == "HIT"


def test_cluster_vs_noncluster_query_branching(client, app_module):

    app_module._test_dummy_cursor.queries.clear()

    # z <= 11 with mode=cluster -> cluster SQL, params include (z,x,y,grid)
    r1 = client.get("/tiles/5/6/7.pbf?mode=cluster")
    assert r1.status_code == 200
    sql1, params1 = app_module._test_dummy_cursor.queries[-1]
    assert "ST_SnapToGrid" in sql1
    assert params1[:3] == (5, 6, 7)
    assert len(params1) == 4  # includes grid

    # z > 11 -> non-cluster SQL, params include (z,x,y,CENTER_LON,CENTER_LAT)
    r2 = client.get("/tiles/12/6/7.pbf?mode=cluster")
    assert r2.status_code == 200
    sql2, params2 = app_module._test_dummy_cursor.queries[-1]
    assert "ST_DistanceSphere" in sql2
    assert params2[:3] == (12, 6, 7)
    assert len(params2) == 5  # includes lon/lat
