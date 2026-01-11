const map = new maplibregl.Map({
    container: 'map',
    style: 'https://demotiles.maplibre.org/style.json',
    center: [0, 0],
    zoom: 2
});

map.on("load", () => {
    map.addSource("points", {
        type: "vector",
        tiles: [
            "http://localhost:8000/tiles/{z}/{x}/{y}.pbf"
        ],
        minzoom: 0,
        maxzoom: 14
    });

    map.addLayer({
    id: "points-layer",
    type: "circle",
    source: "points",
    "source-layer": "points",
    paint: {
        "circle-radius": [
        "interpolate",
        ["linear"],
        ["zoom"],
        0, 2,
        6, 3,
        10, 5
        ],
        "circle-color": "#ff5533",
        "circle-opacity": 0.6
    }
    });


});
/**/ 
