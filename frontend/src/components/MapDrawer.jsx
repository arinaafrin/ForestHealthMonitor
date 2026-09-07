import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet-draw";
import "leaflet-draw/dist/leaflet.draw.css";

const NOMINATIM_URL = "https://nominatim.openstreetmap.org/search";
const SEARCH_DEBOUNCE_MS = 400;

async function searchPlaces(query) {
  const params = new URLSearchParams({
    q: query,
    format: "json",
    polygon_geojson: "1",
    addressdetails: "1",
    limit: "6",
  });

  const response = await fetch(`${NOMINATIM_URL}?${params.toString()}`, {
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error("Place search failed");
  }
  return response.json();
}

export default function MapDrawer({ onBoundaryDrawn }) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const drawnShapesRef = useRef(null);
  const onBoundaryDrawnRef = useRef(onBoundaryDrawn);

  const [searchText, setSearchText] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [isSelectionFill, setIsSelectionFill] = useState(false);

  // Keep the latest callback without re-running the map-init effect.
  useEffect(() => {
    onBoundaryDrawnRef.current = onBoundaryDrawn;
  }, [onBoundaryDrawn]);

  useEffect(() => {
    if (mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current).setView([37.75, -122.45], 12);
    mapInstanceRef.current = map;

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
      maxZoom: 19,
    }).addTo(map);

    const drawnShapes = new L.FeatureGroup();
    map.addLayer(drawnShapes);
    drawnShapesRef.current = drawnShapes;

    const drawControls = new L.Control.Draw({
      draw: {
        polygon: { showArea: false },
        marker: false,
        circle: false,
        circlemarker: false,
        polyline: false,
        rectangle: false,
      },
      edit: { featureGroup: drawnShapes },
    });
    map.addControl(drawControls);

    map.on(L.Draw.Event.CREATED, (event) => {
      drawnShapes.clearLayers();
      drawnShapes.addLayer(event.layer);
      onBoundaryDrawnRef.current(event.layer.toGeoJSON().geometry);
    });

    // Editing an existing
    map.on(L.Draw.Event.EDITED, (event) => {
      event.layers.eachLayer((layer) => {
        onBoundaryDrawnRef.current(layer.toGeoJSON().geometry);
      });
    });

    return () => {
      map.remove();
      mapInstanceRef.current = null;
      drawnShapesRef.current = null;
    };
  }, []);

  // Debounced
  useEffect(() => {
    const query = searchText.trim();
    if (query.length < 3) {
      setSearchResults([]);
      setSearchError("");
      return;
    }

    let cancelled = false;
    setIsSearching(true);
    setSearchError("");

    const timer = setTimeout(async () => {
      try {
        const results = await searchPlaces(query);
        if (!cancelled) setSearchResults(results);
      } catch (err) {
        if (!cancelled) {
          setSearchError("Could not search for that place. Please try again.");
          setSearchResults([]);
        }
      } finally {
        if (!cancelled) setIsSearching(false);
      }
    }, SEARCH_DEBOUNCE_MS);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [searchText]);

  function handleSelectResult(result) {
    const map = mapInstanceRef.current;
    const drawnShapes = drawnShapesRef.current;
    if (!map || !drawnShapes) return;

    drawnShapes.clearLayers();

    const hasPolygon =
      result.geojson &&
      (result.geojson.type === "Polygon" || result.geojson.type === "MultiPolygon");

    if (hasPolygon) {
      const layer = L.geoJSON(result.geojson);
      layer.eachLayer((subLayer) => drawnShapes.addLayer(subLayer));
      map.fitBounds(layer.getBounds(), { maxZoom: 15 });
      onBoundaryDrawnRef.current(result.geojson);
    } else {
      const lat = parseFloat(result.lat);
      const lon = parseFloat(result.lon);
      map.setView([lat, lon], 14);
      onBoundaryDrawnRef.current(null);
    }

    setSearchResults([]);
    setIsSelectionFill(true);
    setSearchText(result.display_name);
  }

  return (
    <div className="relative">
      <div className="relative mb-2">
        <input
          type="text"
          className="w-full border rounded px-3 py-2"
          placeholder="Search for a forest, park, or nature reserve..."
          value={searchText}
          onChange={(e) => {
            setIsSelectionFill(false);
            setSearchText(e.target.value);
          }}
          data-testid="place-search-input"
        />
        {isSearching && (
          <span className="absolute right-3 top-2.5 text-xs text-gray-400">Searching…</span>
        )}

        {searchResults.length > 0 && isSelectionFill === false && (
          <ul
            className="absolute z-[9999] w-full bg-white border rounded shadow mt-1 max-h-56 overflow-auto"
            data-testid="place-search-results"
          >
            {searchResults.map((result) => {
              const hasPolygon =
                result.geojson &&
                (result.geojson.type === "Polygon" || result.geojson.type === "MultiPolygon");
              return (
                <li key={result.place_id}>
                  <button
                    type="button"
                    className="w-full text-left px-3 py-2 hover:bg-gray-100 text-sm"
                    onClick={() => handleSelectResult(result)}
                  >
                    <div className="font-medium">{result.display_name}</div>
                    <div className="text-xs text-gray-500">
                      {hasPolygon ? "Boundary found - will fill in automatically" : "No boundary on file - you'll draw it manually"}
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
        {searchError && (
          <p className="text-severe text-xs mt-1" data-testid="place-search-error">
            {searchError}
          </p>
        )}
      </div>

      <div
        ref={mapContainerRef}
        className="leaflet-map-container w-full"
        data-testid="forest-map"
      />
      <p className="text-xs text-gray-500 mt-1">
        Search above to auto-fill a known boundary, or use the polygon tool on the map to draw
        one by hand. Either way, you can drag the corners to adjust before saving.
      </p>
    </div>
  );
}
