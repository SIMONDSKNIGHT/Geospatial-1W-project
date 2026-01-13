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
    - performance of rendering dots was initially poor, with excessive CPU draw, but has been reduced with usage of psycopg pool to _ as well as optimisations to SQL query.
    - visual clarity at different zoom levels is currently not something addressed, but would likely be improved with a LOD of the map. The points themselves reduce in density with zoom and so remain viewable regardless.

## Tech Selection


### Database
- **PostgreSQL + PostGIS**
  - Stores generated point data in WGS84 (EPSG:4326)
  - /* add something about how the format makes it quick to do operations with
  - PostGIS used as is required of the spec, helping with quick calculations

### Backend
- **Python (FastAPI)**
  - Serves Mapbox Vector Tiles (MVT) on demand
  - Returns the data required for the current map viewport
  - Dockerized

### Frontend
- **MapLibre GL JS**
  - WebGL-based rendering of vector tiles
  - Smooth pan and zoom interactions
  - very basic HTML/JS.

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

3. **Backend Tile Service**
   - Frontend requests tiles using `{z}/{x}/{y}` URLs
   - Backend constructs a tile envelope
   - Points are spatially filtered by bounding box
   - Results are encoded as Mapbox Vector Tiles (PBF)

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


- The application is smooth during pan/zoom (this is not my work, this is )
- Rapid zooming causes database CPU usage spikes due to:
  - Multiple concurrent tile requests
  - Per-tile geometry transformation and MVT encoding
  - resultant effect of sharp unloaded zones when zooming in and out rapidly
    - not dissimilar to own experience when using competitor map services
- This behavior is expected when generating vector tiles on demand without caching or aggregation

### Future Improvements
- Precompute and store geometries to avoid transforming with every request
- add grid-based clustering to reduce calculations
- Optimise database connection pool to reduce connection overhead

---

## Visual Clarity at Scale

in future a LOD system would be beneficial, both for visual clarity (increase detail on ground as camera zooms) as at close zoom levels, lack of local detail impedes navigation, and additionally LOD for points such as grouping them at distance. The advantage of this would be obvious performance increases, at no cost of visual fidelity at those zoom levels.

---


## Trade offs

### Metric correctness vs implementation simplicity

It would be marginally more computationally expensive to figure out whether the variance of a point should be smaller the larger the absolute longitude was for a given point, but for the spec, I decided against it and so we just work with the relative values at the POI

### Vector tiles over pre-clustering

Vector tiles are probably more intensive as the number of points increases but given the spec, thsi technique was used over clustering

### Python over a faster systems language

Python was used as the operational bottleneck while the primary performance bottleneck is on the database side, so I decided to just use the language I was more familiar with.

### MapLibre and plain JS over React

Given the restrictions of the  A framework would be justified for a more application-heavy interface.

### Frontend served by backend container

Serving frontend assets from the backend simplifies deployment and aligns with the take-home scope, at the cost of scalability compared to a dedicated static hosting layer.


## Running Locally


Generate the 100k points first throught the script in scripts
```bash
python scripts/generator.py --n 100000 --center-lat 51.5074 --center-lon -0.1278 --std-km 10  --output-file data/points_100k.csv --seed 42
```

run the below on the TAKEHOMEGDV directory to create dockerised db and backend.
```bash
docker compose up --build
```


## Additional notes

Differences in performance from my own may arise from the platform (likely improvements); Docker image used for the postGIS is amd64, and technically incompatible for MAC, but ran well enough for this project.


## Section on bonus task


### Implementation

Not the cleanest: The points are hardcoded into the main.py as the variables **CENTER_LON** and **CENTER_LAT**, and cannot be changed without a full restart of the environment. Potentially in a full implementation it would make sense to have a settings table that could be changed and then injected into the query, or a point determined and dynamically changed with the distances changing with. An alternative solution was to precalculate the value, but as these would only calculate for 1 point each time, I thought calculating it through the query was not a poor compromise.