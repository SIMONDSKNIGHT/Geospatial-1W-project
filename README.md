### TakeHomeGDV
Take home task for demonstration of technical skills.

# Geospatial Data Visualisation App
Project that aligns to the criteria listed in the take home assessment requirements.:
-   **Sampling of 100000 locations**
    - Completed to spec, sampled using bivariate normal distribution with Standard Deviation of 10km
    - Centered around London: **LAT 51.5074 LON -0.1278**
    - generation of points utilises deviation on metres, not on lon/lat.
- **Data stored in PostGIS**
    - uses predictable schema of GEOM with additional values for debugging
- **Frontend**
    - interactive map interface with panning, zooming completed with the help of maplibre.
    - performance of rendering dots was initially poor, with excessive CPU draw, but has been reduced with usage of psycopg pool as well as optimisations to SQL query and tile generation.
    - visual clarity at different zoom levels is now partially addressed through a simple LOD-style approach using server-side grid-based clustering.
    - clustering can be toggled on and off from the frontend, and is automatically disabled above a certain zoom level so individual points can still be inspected without ambiguity.

## Tech Selection


### Database
- **PostgreSQL + PostGIS**
  - Stores generated point data in WGS84 (EPSG:4326) 
  - PostGIS used as required by the spec, allowing for fast spatial filtering, distance calculations, and geometry operations directly in the database.
  - geometry is additionally stored in EPSG:3857 to speed up recall during tile generation and spatial filtering.

### Backend
- **Python (FastAPI)**
  - Serves Mapbox Vector Tiles (MVT) on demand
  - Returns the data required for the current map viewport
  - Dockerized
  - lightweight tile caching used to reduce repeated tile generation during normal interaction
  - server side clustering logic to reduce feature counts at low zoom levels

### Frontend
- **MapLibre GL JS**
  - WebGL-based rendering of vector tiles
  - Smooth pan and zoom interactions
  - basic HTML/JS.
  - clustering toggle rebuilds the vector tile source to explicitly request clustered or raw tiles from the backend

### Infrastructure
- **Docker & Docker Compose**
  - 1. PostGIS database container
  - 2. Backend API container (currently hosts frontend)

## Architecture

1. **Data Generation**
   - Points are sampled from a bivariate normal distribution
   - Centered on London (**LAT 51.5074 LON -0.1278** )
   - Standard deviation: 10 km longitude and latitude directions
   - Coordinates stored in EPSG:4326 (WGS84)

2. **Storage**
   - Points stored in a PostGIS table with a geometry column
   - GiST spatial index used for fast bounding-box queries
   - additional geometry stored in EPSG:3857 to support efficient tile envelope filtering without runtime reprojection

3. **Backend Tile Service**
   - Frontend requests tiles using `{z}/{x}/{y}` URLs
   - Backend constructs a tile envelope in Web Mercator
   - Points are spatially filtered by bounding box
   - Results are encoded as Mapbox Vector Tiles (PBF)
   - optional grid-based aggregation is applied at lower zoom levels when clustering is enabled
   - clustered and raw tiles are cached independently to avoid stale results when toggling modes

4. **Frontend Rendering**
   - MapLibre requests tiles based on viewport and zoom level
   - Points rendered as circle layers on a basemap
   - Rendering handled entirely on the GPU via WebGL
   - CURRENTLY loaded and hosted by backend container (cheap solution was acceptable for 6-8 hour takehome task)


## Performance Optimizations

### Implemented
- **Vector tiles**
  - only visible data transferred to the client
  - Minimizes network usage and browser memory footprint
- **Spatial indexing (GiST)**
  - Efficient bounding-box filtering in PostGIS
- **Viewport-driven loading**
  - No full-dataset fetch at any point
- **Server-side grid-based clustering**
  - Points grouped using a simple spatial grid at low zoom levels
  - Reduces number of features returned per tile and lowers draw overhead
  - Automatically disabled above a defined zoom threshold
- **In-memory tile caching**
  - Frequently requested tiles cached in-process
  - Cache key includes tile coordinates and render mode (clustered vs raw)
  - Significantly reduces redundant database work during panning and repeated navigation

- The application is smooth during pan/zoom (this is largely MapLibre/WebGL doing the heavy lifting)
- Rapid zooming can still cause database CPU usage spikes due to:
  - Multiple concurrent tile requests
  - Per-tile geometry filtering and MVT encoding
  - resultant effect of sharp unloaded zones when zooming in and out rapidly
    - not dissimilar to own experience when using competitor map services
- This behaviour is expected when generating vector tiles on demand, even with caching, under aggressive interaction patterns

### Future Improvements
- Precompute and store additional aggregates for very low zoom levels
- move tile caching out of process (e.g. Redis or CDN-backed)
- further tune grid sizes per zoom level
- decouple frontend hosting from backend API

### Attempted improvements
- Some attempt made at trying to get more complex LOD behaviour. While functional, this caused noticeable choppiness during zooming and was removed in favour of a simpler, more predictable grid-based approach.

---

## Visual Clarity at Scale

At large scales (zoomed out), visual clarity benefits from grouping points to avoid excessive overlap and overdraw. This is now partially addressed via optional server-side clustering, which improves readability and performance when viewing the dataset at distance.

At closer zoom levels, clustering is disabled so individual points remain visible and interactable, preserving local detail and usability.

---


## Trade offs

### Metric correctness vs implementation simplicity

It would be more computationally expensive to account for longitudinal distortion. For the purposes of a takehome task, distances and deviations are instead treated relative to the point of interest.

### Vector tiles over pre-clustering

Vector tiles generated on demand are more computationally expensive as dataset size grows, but this approach was chosen over absoluete clustering to keep the pipeline flexible and implementation time reasonable.

### Python over a faster systems language

Python was used in spite of slower speed as because  primary performance bottleneck is on the database side, any difference in the code speed was marginal. My greater familiarity with python and FastAPI allowed faster development without materially impacting overall system performance.

### MapLibre and plain JS over frontend framework

Aa framework was not introduced. Plain JS was sufficient and looks pretty good to boot. but is inflexible

### Frontend served by backend container

deploying frontend from the backend simplifies deployment and aligns with the take home scope at the cost of scalability compared to a dedicated static hosting layer, and also looking very ugly


## Running Locally


Generate the 100k points first throught the script in scripts
```bash
python scripts/generator.py --n 100000 --center-lat 51.5074 --center-lon -0.1278 --std-km 10  --output-file data/points_100k.csv --seed 42
```
then 
```bash
docker compose up --build
```