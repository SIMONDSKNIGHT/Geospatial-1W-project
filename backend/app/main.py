import os
import time
from collections import OrderedDict
from threading import Lock

from fastapi import FastAPI, Query, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from psycopg_pool import ConnectionPool

DEFAULT_CENTER_LON = -0.1278
DEFAULT_CENTER_LAT = 51.5074

CENTER_LON = float(os.environ.get("CENTER_LON", DEFAULT_CENTER_LON))
CENTER_LAT = float(os.environ.get("CENTER_LAT", DEFAULT_CENTER_LAT))
DB_URL = os.environ.get("DATABASE_URL", "postgresql://psql:password@db:5432/mydatabase")

# ------ Cache Setup -----

CACHE_MAX_TILES = int(os.environ.get("TILE_CACHE_MAX", "2000"))
CACHE_TTL_SECONDS = int(os.environ.get("TILE_CACHE_TTL", "300"))

_tile_cache: OrderedDict[tuple[int, int, int], tuple[float, bytes]] = OrderedDict()
_cache_lock = Lock()


def cache_get(key: tuple[int, int, int]) -> bytes | None:
    now = time.time()
    with _cache_lock:
        entry = _tile_cache.get(key)
        if entry is None:
            return None

        expires_at, value = entry
        if expires_at < now:
            _tile_cache.pop(key, None)
            return None

        # refresh LRU
        _tile_cache.move_to_end(key, last=True)
        return value


def cache_set(key: tuple[int, int, int], value: bytes) -> None:
    expires_at = time.time() + CACHE_TTL_SECONDS
    with _cache_lock:
        _tile_cache[key] = (expires_at, value)
        _tile_cache.move_to_end(key, last=True)

        while len(_tile_cache) > CACHE_MAX_TILES:
            _tile_cache.popitem(last=False)


# ------ APP SETUP -----

app = FastAPI()
# Just for low overhead serving of frontend files without dedicated container
app.mount("/static", StaticFiles(directory="frontend"), name="frontend")


@app.get("/")
def serve_index():
    return FileResponse("frontend/index.html")



@app.get("/health")
def health_check():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
    return {"status": "ok"}

# ----- Database connection pool -----
pool = ConnectionPool(conninfo=DB_URL, min_size=1, max_size=10)


def get_db_connection():
    return pool.connection()


@app.get("/tiles/{z}/{x}/{y}.pbf")
def get_tile(z: int, x: int, y: int, mode: str = Query("cluster")):
    key = (z, x, y, mode)  

    #Cache check
    cached = cache_get(key)
    if cached is not None:
        return Response(
            content=cached,
            media_type="application/x-protobuf",
            headers={
                "X-Cache": "HIT",
                "Cache-Control": "public, max-age=300",
            },
        )
    sql = """
WITH env AS (
    SELECT ST_TileEnvelope(%s, %s, %s) AS geom_3857
),
temp AS (
    SELECT
        id,
        ST_DistanceSphere(
            public.points.geom_4326,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326)
        ) AS dist_m,
        ST_AsMVTGeom(
            public.points.geom_3857,
            env.geom_3857,
            4096,
            0,
            true
        ) AS geom
    FROM public.points
    CROSS JOIN env
    WHERE public.points.geom_3857 && env.geom_3857
)
SELECT ST_AsMVT(temp, 'points', 4096, 'geom') AS mvt
FROM temp;
"""

    sql_cluster = """
WITH env AS (
    SELECT ST_TileEnvelope(%s, %s, %s) AS geom_3857
),
temp AS (
    SELECT
        COUNT(*) AS count,
        ST_AsMVTGeom(
            ST_Centroid(ST_Collect(public.points.geom_3857)),
            env.geom_3857,
            4096,
            0,
            true
        ) AS geom
    FROM public.points
    CROSS JOIN env
    WHERE public.points.geom_3857 && env.geom_3857
    GROUP BY ST_SnapToGrid(public.points.geom_3857, %s), env.geom_3857  -- FIX: include env.geom_3857 so it's legal
)
SELECT ST_AsMVT(temp, 'points', 4096, 'geom') AS mvt
FROM temp;
"""
    CLUSTER_MAX_ZOOM = 11
    grid = max(50, 2000 - 150 * z)  # meters; tune constants


    if mode == "cluster" and z <= CLUSTER_MAX_ZOOM:
        sql_to_run = sql_cluster
        grid = max(50, 2000 - 150 * z)  # or whatever you pick
        params = (z, x, y, grid)
    else:
        sql_to_run = sql
        params = (z, x, y, CENTER_LON, CENTER_LAT)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql_to_run, params)

            row = cur.fetchone()
            mvt_data = row[0] if row and row[0] else b""

    cache_set(key, mvt_data)

    return Response(
        content=mvt_data,
        media_type="application/x-protobuf",
        headers={
            "X-Cache": "MISS",
            "Cache-Control": "public, max-age=300",
        },
    )
