

CREATE TABLE public.points (
    id SERIAL PRIMARY KEY,
    geom GEOMETRY(Point, 4326), -- WGS84
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX points_geom_idx ON public.points USING GIST (geom);

