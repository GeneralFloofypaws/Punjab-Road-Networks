
import { useEffect, useMemo, useState } from "react";
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import "./App.css";

const ROAD_COLORS = {
  NH: "#e63946",
  SH: "#f4a261",
  MDR: "#457b9d",
  ODR: "#2a9d8f",
  OTHER: "#888888",
};

const JUNCTION_COLORS = {
  NH: "#e63946",
  SH: "#f4a261",
  MDR: "#457b9d",
  ODR: "#2a9d8f",
  OTHER: "#888888",
  UNKNOWN: "#aaaaaa",
};

const CATEGORIES = ["NH", "SH", "MDR", "ODR", "OTHER"];

function escapeHTML(value) {
  return String(value ?? "N/A").replace(
    /[&<>"']/g,
    (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    })[char]
  );
}

function FitBounds({ segments, junctions }) {
  const map = useMap();

  useEffect(() => {
    if (!segments || !junctions) return;

    const bounds = L.geoJSON([
      segments,
      junctions,
    ]).getBounds();

    if (bounds.isValid()) {
      map.fitBounds(bounds.pad(0.05));
    }
  }, [segments, junctions, map]);

  return null;
}

function segmentStyle(feature) {
  const category = feature.properties?.road_category || "OTHER";

  return {
    color: ROAD_COLORS[category] || ROAD_COLORS.OTHER,
    weight: category === "NH" ? 4 : 3,
    opacity: 0.85,
  };
}

function segmentPopup(feature, layer) {
  const p = feature.properties || {};

  layer.bindPopup(`
    <div class="map-popup">
      <h3>Road Segment</h3>
      <p><b>Reference:</b> ${escapeHTML(p.road_ref)}</p>
      <p><b>Category:</b> ${escapeHTML(p.road_category)}</p>
      <p><b>Functional class:</b> ${escapeHTML(p.fclass)}</p>
      <p><b>Length:</b> ${Number(p.length_m || 0).toFixed(2)} m</p>
      <p><b>Bridge:</b> ${escapeHTML(p.bridge)}</p>
      <p><b>Tunnel:</b> ${escapeHTML(p.tunnel)}</p>
      <p><b>Layer:</b> ${escapeHTML(p.layer)}</p>
      <p><b>Segment ID:</b> ${escapeHTML(p.segment_id)}</p>
    </div>
  `);
}

function junctionPoint(feature, latlng) {
  const p = feature.properties || {};
  const category = String(p.road_combo_class || "UNKNOWN")
    .split("-")[0];

  return L.circleMarker(latlng, {
    radius: 6,
    fillColor: JUNCTION_COLORS[category] || "#aaaaaa",
    color: "#ffffff",
    weight: 1.5,
    opacity: 1,
    fillOpacity: 0.95,
  });
}

function junctionPopup(feature, layer) {
  const p = feature.properties || {};

  layer.bindPopup(`
    <div class="map-popup">
      <h3>Junction</h3>
      <p><b>ID:</b> ${escapeHTML(p.junction_id)}</p>
      <p><b>Road combination:</b> ${escapeHTML(p.road_combo_class)}</p>
      <p><b>Topology:</b> ${escapeHTML(p.topology_type)}</p>
      <p><b>Connected roads:</b> ${escapeHTML(p.connected_road_count)}</p>
      <p><b>Incident segments:</b> ${escapeHTML(p.incident_segment_count)}</p>
      <p><b>Road references:</b> ${escapeHTML(p.connected_road_refs)}</p>
      <p><b>Functional classes:</b> ${escapeHTML(p.connected_fclasses)}</p>
    </div>
  `);
}

export default function App() {
  const [segments, setSegments] = useState(null);
  const [junctions, setJunctions] = useState(null);
  const [visibleCategories, setVisibleCategories] = useState(
    new Set(CATEGORIES)
  );
  const [showJunctions, setShowJunctions] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadData() {
      try {
        const [segmentResponse, junctionResponse] = await Promise.all([
          fetch("/data/segments.geojson"),
          fetch("/data/junctions_classified.geojson"),
        ]);

        if (!segmentResponse.ok || !junctionResponse.ok) {
          throw new Error("Could not load GeoJSON files.");
        }

        const [segmentData, junctionData] = await Promise.all([
          segmentResponse.json(),
          junctionResponse.json(),
        ]);

        setSegments(segmentData);
        setJunctions(junctionData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const filteredSegments = useMemo(() => {
    if (!segments) return null;

    return {
      ...segments,
      features: segments.features.filter((feature) => {
        const category = feature.properties?.road_category || "OTHER";
        return visibleCategories.has(category);
      }),
    };
  }, [segments, visibleCategories]);

  function toggleCategory(category) {
    setVisibleCategories((previous) => {
      const next = new Set(previous);

      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }

      return next;
    });
  }

  if (loading) {
    return <div className="status-screen">Loading road network...</div>;
  }

  if (error) {
    return <div className="status-screen error">{error}</div>;
  }

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">R</div>
          <div>
            <h1>PunjabRoad</h1>
            <p>Road Network Intelligence</p>
          </div>
        </div>

        <section className="panel-section">
          <h2>Network Overview</h2>

          <div className="stat-grid">
            <div className="stat-card">
              <strong>{junctions.features.length}</strong>
              <span>Junctions</span>
            </div>

            <div className="stat-card">
              <strong>{segments.features.length}</strong>
              <span>Segments</span>
            </div>
          </div>
        </section>

        <section className="panel-section">
          <h2>Road Categories</h2>

          {CATEGORIES.map((category) => (
            <label className="toggle-row" key={category}>
              <span className="category-name">
                <span
                  className="legend-dot"
                  style={{ background: ROAD_COLORS[category] }}
                />
                {category}
              </span>

              <input
                type="checkbox"
                checked={visibleCategories.has(category)}
                onChange={() => toggleCategory(category)}
              />
            </label>
          ))}
        </section>

        <section className="panel-section">
          <h2>Junctions</h2>

          <label className="toggle-row">
            <span>Show junction markers</span>
            <input
              type="checkbox"
              checked={showJunctions}
              onChange={(e) => setShowJunctions(e.target.checked)}
            />
          </label>
        </section>

        <div className="sidebar-footer">
          <span className="status-dot" />
          Network data loaded
        </div>
      </aside>

      <main className="map-area">
        <div className="map-header">
          <div>
            <h2>Punjab Road Network</h2>
            <p>Interactive road and junction explorer</p>
          </div>
        </div>

        <MapContainer
          center={[30.9, 75.85]}
          zoom={10}
          className="map-container"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <FitBounds
            segments={segments}
            junctions={junctions}
          />

          {filteredSegments && (
            <GeoJSON
              key={Array.from(visibleCategories).sort().join("-")}
              data={filteredSegments}
              style={segmentStyle}
              onEachFeature={segmentPopup}
            />
          )}

          {showJunctions && (
            <GeoJSON
              key="junction-layer"
              data={junctions}
              pointToLayer={junctionPoint}
              onEachFeature={junctionPopup}
            />
          )}
        </MapContainer>
      </main>
    </div>
  );
}
