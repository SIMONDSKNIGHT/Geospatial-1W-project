import os
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import psycopg

app = FastAPI()
# Just for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_URL = os.environ.get("DB_URL", "postgresql://psql:password@db:5432/mydatabase")

@app.get("/health")
def health_check():
    return {"status": "ok"}

def get_db_connection():
    return psycopg.connect(DB_URL)

@app.get("/tiles/{z}/{x}/{y}.pbf")
def get_tile(z: int, x: int, y: int):
    sql = """
WITH 
    env AS (
        SELECT ST_TileEnvelope(%s, %s, %s) AS geom_3857
    ),
    temp AS (
        SELECT
            id,
            ST_AsMVTGeom(
                ST_Transform(geom, 3857), env.geom_3857
            ) AS geom
        FROM public.points
        CROSS JOIN env
        WHERE ST_Intersects(ST_Transform(points.geom, 3857), env.geom_3857)
    )
SELECT ST_AsMVT(temp.*, 'points', 4096, 'geom') AS mvt FROM temp;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (z, x, y))
            row = cur.fetchone()
            mvt_data = row[0] if row and row[0] else None
        if not mvt_data:
            return Response(content=b"", media_type="application/x-protobuf")

    return Response(content=mvt_data, media_type="application/x-protobuf")