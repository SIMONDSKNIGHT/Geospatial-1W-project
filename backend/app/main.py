import os
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import psycopg
from psycopg_pool import ConnectionPool

CENTER_LON = -0.1278
CENTER_LAT = 51.5074

app = FastAPI()
# Just for low overhead serving of frontend files without dedicated container
app.mount("/static", StaticFiles(directory="frontend"), name="frontend")
@app.get("/")
def serve_index():
    return FileResponse("frontend/index.html")

DB_URL = os.environ.get("DB_URL", "postgresql://psql:password@db:5432/mydatabase")

@app.get("/health")
def health_check():
    return {"status": "ok"}

pool = ConnectionPool(conninfo=DB_URL, min_size=1, max_size=10)
def get_db_connection():
    return pool.connection()

@app.get("/tiles/{z}/{x}/{y}.pbf")
def get_tile(z: int, x: int, y: int):
    # if z >= 11:
    #     grid = None
    # else:
    #     base = 0.5
    #     grid = base / (2 ** z)
    sql1 = """
    WITH env AS (
        SELECT ST_TileEnvelope(%s, %s, %s) AS geom_3857,
               ST_Transform(ST_TileEnvelope(%s, %s, %s), 4326) AS geom_4326
    ),
    temp AS (
        SELECT
            id,
            ST_DistanceSphere(
                public.points.geom,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)
            ) AS dist_m,
            ST_AsMVTGeom(
                ST_Transform(public.points.geom, 3857), env.geom_3857, 4096, 0, true
            ) AS geom
        FROM public.points
        CROSS JOIN env
        WHERE public.points.geom && env.geom_4326
    )
    SELECT ST_AsMVT(temp.*, 'points', 4096, 'geom') AS mvt FROM temp;
    """
    # sql2 = """
    # WITH env AS (
    #     SELECT ST_TileEnvelope(%s, %s, %s) AS geom_3857,
    #            ST_Transform(ST_TileEnvelope(%s, %s, %s), 4326) AS geom_4326
    # ),
    # buckets AS (
    #     SELECT
    #         ST_SnapToGrid(public.points.geom, %s) AS cell,
    #         COUNT(*) AS n,
    #         ST_Centroid(ST_Collect(public.points.geom)) AS centroid_4326
    #     FROM public.points
    #     CROSS JOIN env
    #     WHERE public.points.geom && env.geom_4326
    #     GROUP BY cell
    # ),
    # temp AS (
    #     SELECT
    #         n,
    #         ST_DistanceSphere(
    #             centroid_4326,
    #             ST_SetSRID(ST_MakePoint(%s, %s), 4326)
    #         ) AS dist_m,
    #         ST_AsMVTGeom(
    #             ST_Transform(centroid_4326, 3857), env.geom_3857, 4096, 0, true
    #         ) AS geom
    #     FROM buckets
    #     CROSS JOIN env
    # )
    # SELECT ST_AsMVT(temp.*, 'points', 4096, 'geom') AS mvt FROM temp;
    # """
    grid = None # LOD currently non-functional
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if grid:
                #sql = sql2
                params = (z, x, y, z, x, y, grid, CENTER_LON, CENTER_LAT)
            else:
                sql = sql1
                params = (z, x, y, z, x, y, CENTER_LON, CENTER_LAT)
            cur.execute(sql, params)
            row = cur.fetchone()
            mvt_data = row[0] if row and row[0] else None
        if not mvt_data:
            return Response(content=b"", media_type="application/x-protobuf")

    return Response(content=mvt_data, media_type="application/x-protobuf")