import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import type { ParcelDetail } from '../types/cadastral';

interface CadastralMapProps {
  selectedParcel?: ParcelDetail | null;
  onSelectParcelId?: (parcelId: string) => void;
  showLegacy?: boolean;
  showDrone?: boolean;
  showGnss?: boolean;
  showReconciled?: boolean;
  onToggleLayer?: (layer: 'legacy' | 'drone' | 'gnss' | 'reconciled') => void;
  standalone?: boolean;
}

export const CadastralMap: React.FC<CadastralMapProps> = ({
  selectedParcel,
  showLegacy = true,
  showDrone = true,
  showGnss = true,
  showReconciled = true,
  onToggleLayer
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  
  // Layer groups for dynamic toggling & updates
  const legacyLayerGroup = useRef<L.LayerGroup>(L.layerGroup());
  const droneLayerGroup = useRef<L.LayerGroup>(L.layerGroup());
  const gnssLayerGroup = useRef<L.LayerGroup>(L.layerGroup());
  const reconciledLayerGroup = useRef<L.LayerGroup>(L.layerGroup());

  // Initialize Leaflet Map
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    // Centered around the demo Hinjewadi/Pune region
    const map = L.map(mapContainer.current, {
      center: [18.5910, 73.7380],
      zoom: 17,
      zoomControl: false
    });

    L.control.zoom({ position: 'topright' }).addTo(map);

    // OpenStreetMap standard tile layer (free, no API key needed)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    // Add layer groups to map
    legacyLayerGroup.current.addTo(map);
    droneLayerGroup.current.addTo(map);
    gnssLayerGroup.current.addTo(map);
    reconciledLayerGroup.current.addTo(map);

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update GeoJSON features when selected parcel changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Clear previous layers
    legacyLayerGroup.current.clearLayers();
    droneLayerGroup.current.clearLayers();
    gnssLayerGroup.current.clearLayers();
    reconciledLayerGroup.current.clearLayers();

    if (!selectedParcel) return;

    const bounds = L.latLngBounds([]);

    // 1. Legacy Geometry (Blue)
    if (selectedParcel.geometry_geojson) {
      const legacyGeo = L.geoJSON(selectedParcel.geometry_geojson, {
        style: {
          color: '#1d4ed8',
          weight: 2,
          dashArray: '5, 5',
          fillColor: '#3b82f6',
          fillOpacity: 0.15
        }
      });
      legacyLayerGroup.current.addLayer(legacyGeo);
      try {
        bounds.extend(legacyGeo.getBounds());
      } catch (e) {}
    }

    // 2. Drone Geometry (Amber)
    if (selectedParcel.drone_geometry_geojson) {
      const droneGeo = L.geoJSON(selectedParcel.drone_geometry_geojson, {
        style: {
          color: '#d97706',
          weight: 2.5,
          fillColor: '#f59e0b',
          fillOpacity: 0.2
        }
      });
      droneLayerGroup.current.addLayer(droneGeo);
      try {
        bounds.extend(droneGeo.getBounds());
      } catch (e) {}
    }

    // 3. Reconciled Geometry (Emerald Green)
    if (selectedParcel.reconciled_geometry_geojson) {
      const recGeo = L.geoJSON(selectedParcel.reconciled_geometry_geojson, {
        style: {
          color: '#059669',
          weight: 3,
          fillColor: '#10b981',
          fillOpacity: 0.25
        }
      });
      reconciledLayerGroup.current.addLayer(recGeo);
      try {
        bounds.extend(recGeo.getBounds());
      } catch (e) {}
    }

    // 4. GNSS Points (Red Circle Markers)
    if (selectedParcel.gnss_points && selectedParcel.gnss_points.length > 0) {
      selectedParcel.gnss_points.forEach((pt) => {
        const marker = L.circleMarker([pt.latitude, pt.longitude], {
          radius: 5,
          fillColor: '#ef4444',
          color: '#ffffff',
          weight: 1.5,
          fillOpacity: 0.95
        });
        marker.bindPopup(`<b>GNSS Point:</b> ${pt.point_id}<br/><b>Accuracy:</b> ±${pt.accuracy_m}m`);
        gnssLayerGroup.current.addLayer(marker);
        bounds.extend([pt.latitude, pt.longitude]);
      });
    }

    // Fit map bounds to selected parcel geometry
    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [60, 60], maxZoom: 18 });
    }
  }, [selectedParcel]);

  // Handle layer visibility toggles
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (showLegacy) {
      if (!map.hasLayer(legacyLayerGroup.current)) legacyLayerGroup.current.addTo(map);
    } else {
      if (map.hasLayer(legacyLayerGroup.current)) map.removeLayer(legacyLayerGroup.current);
    }

    if (showDrone) {
      if (!map.hasLayer(droneLayerGroup.current)) droneLayerGroup.current.addTo(map);
    } else {
      if (map.hasLayer(droneLayerGroup.current)) map.removeLayer(droneLayerGroup.current);
    }

    if (showGnss) {
      if (!map.hasLayer(gnssLayerGroup.current)) gnssLayerGroup.current.addTo(map);
    } else {
      if (map.hasLayer(gnssLayerGroup.current)) map.removeLayer(gnssLayerGroup.current);
    }

    if (showReconciled) {
      if (!map.hasLayer(reconciledLayerGroup.current)) reconciledLayerGroup.current.addTo(map);
    } else {
      if (map.hasLayer(reconciledLayerGroup.current)) map.removeLayer(reconciledLayerGroup.current);
    }
  }, [showLegacy, showDrone, showGnss, showReconciled]);

  return (
    <div className="relative w-full h-full min-h-[420px] bg-slate-100 overflow-hidden border border-slate-200">
      <div ref={mapContainer} className="w-full h-full absolute inset-0 z-0" />

      {/* Layer Control Bar: Only Legacy, Drone, GNSS, Reconciled */}
      {onToggleLayer && (
        <div className="absolute top-3 left-3 z-[1000] bg-white/95 backdrop-blur-sm border border-slate-300 shadow-sm rounded px-3 py-2 flex items-center gap-4 text-xs font-medium text-slate-700 select-none">
          <span className="text-slate-400 uppercase tracking-wider text-[10px] font-semibold mr-1">Layers:</span>
          
          <label className="flex items-center gap-1.5 cursor-pointer hover:text-blue-800">
            <input
              type="checkbox"
              checked={showLegacy}
              onChange={() => onToggleLayer('legacy')}
              className="rounded border-slate-300 text-blue-700 focus:ring-0"
            />
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-sm bg-blue-600/30 border border-blue-700 inline-block" />
              Legacy
            </span>
          </label>

          <label className="flex items-center gap-1.5 cursor-pointer hover:text-amber-800">
            <input
              type="checkbox"
              checked={showDrone}
              onChange={() => onToggleLayer('drone')}
              className="rounded border-slate-300 text-amber-600 focus:ring-0"
            />
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-sm bg-amber-500/30 border border-amber-600 inline-block" />
              Drone
            </span>
          </label>

          <label className="flex items-center gap-1.5 cursor-pointer hover:text-red-800">
            <input
              type="checkbox"
              checked={showGnss}
              onChange={() => onToggleLayer('gnss')}
              className="rounded border-slate-300 text-red-600 focus:ring-0"
            />
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block border border-white" />
              GNSS
            </span>
          </label>

          <label className="flex items-center gap-1.5 cursor-pointer hover:text-emerald-800">
            <input
              type="checkbox"
              checked={showReconciled}
              onChange={() => onToggleLayer('reconciled')}
              className="rounded border-slate-300 text-emerald-600 focus:ring-0"
            />
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500/40 border border-emerald-700 inline-block" />
              Reconciled
            </span>
          </label>
        </div>
      )}

      {/* Coordinate / CRS Badge */}
      <div className="absolute bottom-2 left-3 z-[1000] bg-white/90 text-[10px] text-slate-500 px-2 py-0.5 rounded border border-slate-200 shadow-xs">
        Leaflet GIS Engine | CRS: EPSG:4326 | OpenStreetMap
      </div>
    </div>
  );
};
