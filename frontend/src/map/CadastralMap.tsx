import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import type { ParcelDetail } from '../types/cadastral';
import { getParcelsGeoJSON } from '../services/api';
import { Maximize2, Crosshair } from 'lucide-react';

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
  onSelectParcelId,
  showLegacy = true,
  showDrone = true,
  showGnss = true,
  showReconciled = true,
  onToggleLayer
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);

  const [showFabric, setShowFabric] = useState(true);
  const [fabricBounds, setFabricBounds] = useState<L.LatLngBounds | null>(null);
  const [selectedBounds, setSelectedBounds] = useState<L.LatLngBounds | null>(null);

  // Layer groups for dynamic toggling & updates
  const fabricLayerGroup = useRef<L.LayerGroup>(L.layerGroup());
  const legacyLayerGroup = useRef<L.LayerGroup>(L.layerGroup());
  const droneLayerGroup = useRef<L.LayerGroup>(L.layerGroup());
  const gnssLayerGroup = useRef<L.LayerGroup>(L.layerGroup());
  const reconciledLayerGroup = useRef<L.LayerGroup>(L.layerGroup());

  // Keep a ref to onSelectParcelId to avoid recreating layers when callback changes
  const onSelectRef = useRef(onSelectParcelId);
  useEffect(() => {
    onSelectRef.current = onSelectParcelId;
  }, [onSelectParcelId]);

  // 1. Initialize Leaflet Map
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    // Centered around Coimbatore Corporation, Tamil Nadu
    const map = L.map(mapContainer.current, {
      center: [11.0168, 76.9558],
      zoom: 17,
      zoomControl: false
    });

    L.control.zoom({ position: 'topright' }).addTo(map);

    // OpenStreetMap standard tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    // Add layer groups to map in rendering order
    fabricLayerGroup.current.addTo(map);
    legacyLayerGroup.current.addTo(map);
    droneLayerGroup.current.addTo(map);
    gnssLayerGroup.current.addTo(map);
    reconciledLayerGroup.current.addTo(map);

    mapRef.current = map;

    // 2. Fetch Full Cadastral Fabric GeoJSON (all 300 parcels)
    getParcelsGeoJSON()
      .then((geojson) => {
        if (!mapRef.current) return;
        fabricLayerGroup.current.clearLayers();

        const geoJsonLayer = L.geoJSON(geojson, {
          style: (feature) => {
            const isConflict = feature?.properties?.status === 'Conflict';
            return {
              color: isConflict ? '#f59e0b' : '#64748b',
              weight: isConflict ? 1.5 : 1,
              dashArray: isConflict ? '3, 3' : undefined,
              fillColor: isConflict ? '#fbbf24' : '#94a3b8',
              fillOpacity: 0.12
            };
          },
          onEachFeature: (feature, layer) => {
            if (feature.properties) {
              const pId = feature.properties.parcel_id;
              const sNo = feature.properties.full_survey || feature.properties.survey_no;
              const status = feature.properties.status;
              const conf = (feature.properties.confidence_pct || 0).toFixed(1);

              layer.bindTooltip(
                `<div class="font-sans text-xs">
                  <b>Parcel ${pId} (Survey ${sNo})</b><br/>
                  Status: <span class="${status === 'Conflict' ? 'text-amber-600 font-bold' : 'text-emerald-600 font-bold'}">${status}</span><br/>
                  Confidence: <b>${conf}%</b>
                </div>`,
                { sticky: true }
              );

              layer.on('click', () => {
                if (onSelectRef.current) {
                  onSelectRef.current(pId);
                }
              });
            }
          }
        });

        fabricLayerGroup.current.addLayer(geoJsonLayer);

        try {
          const b = geoJsonLayer.getBounds();
          if (b.isValid()) {
            setFabricBounds(b);
            if (!selectedParcel) {
              map.fitBounds(b, { padding: [30, 30] });
            }
          }
        } catch (e) {}
      })
      .catch((err) => console.error('Failed to load full parcel fabric:', err));

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // 3. Update Selected Parcel Geometries
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Clear previous selected layers
    legacyLayerGroup.current.clearLayers();
    droneLayerGroup.current.clearLayers();
    gnssLayerGroup.current.clearLayers();
    reconciledLayerGroup.current.clearLayers();

    if (!selectedParcel) {
      setSelectedBounds(null);
      return;
    }

    const bounds = L.latLngBounds([]);

    // 1. Legacy Geometry (Blue)
    if (selectedParcel.geometry_geojson) {
      const legacyGeo = L.geoJSON(selectedParcel.geometry_geojson, {
        style: {
          color: '#1d4ed8',
          weight: 2.5,
          dashArray: '5, 5',
          fillColor: '#3b82f6',
          fillOpacity: 0.2
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
          weight: 3,
          fillColor: '#f59e0b',
          fillOpacity: 0.25
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
          weight: 3.5,
          fillColor: '#10b981',
          fillOpacity: 0.3
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
          radius: 6,
          fillColor: '#ef4444',
          color: '#ffffff',
          weight: 2,
          fillOpacity: 0.95
        });
        marker.bindPopup(`<b>GNSS Point:</b> ${pt.point_id}<br/><b>Accuracy:</b> ±${pt.accuracy_m}m`);
        gnssLayerGroup.current.addLayer(marker);
        bounds.extend([pt.latitude, pt.longitude]);
      });
    }

    if (bounds.isValid()) {
      setSelectedBounds(bounds);
      map.fitBounds(bounds, { padding: [60, 60], maxZoom: 18 });
    }
  }, [selectedParcel]);

  // 4. Handle Layer Visibility Toggles
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (showFabric) {
      if (!map.hasLayer(fabricLayerGroup.current)) fabricLayerGroup.current.addTo(map);
    } else {
      if (map.hasLayer(fabricLayerGroup.current)) map.removeLayer(fabricLayerGroup.current);
    }

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
  }, [showFabric, showLegacy, showDrone, showGnss, showReconciled]);

  const fitFabric = () => {
    if (mapRef.current && fabricBounds && fabricBounds.isValid()) {
      mapRef.current.fitBounds(fabricBounds, { padding: [30, 30] });
    }
  };

  const fitSelected = () => {
    if (mapRef.current && selectedBounds && selectedBounds.isValid()) {
      mapRef.current.fitBounds(selectedBounds, { padding: [60, 60], maxZoom: 18 });
    }
  };

  return (
    <div className="relative w-full h-full min-h-[420px] bg-slate-100 overflow-hidden border border-slate-200">
      <div ref={mapContainer} className="w-full h-full absolute inset-0 z-0" />

      {/* Layer Control Bar with Full Fabric Toggle */}
      <div className="absolute top-3 left-3 z-[1000] bg-white/95 backdrop-blur-xs border border-slate-300 shadow-sm rounded px-3 py-2 flex flex-wrap items-center gap-4 text-xs font-medium text-slate-700 select-none">
        <span className="text-slate-400 uppercase tracking-wider text-[10px] font-semibold mr-1">Layers:</span>

        {/* Full Fabric Toggle */}
        <label className="flex items-center gap-1.5 cursor-pointer hover:text-slate-900">
          <input
            type="checkbox"
            checked={showFabric}
            onChange={(e) => setShowFabric(e.target.checked)}
            className="rounded border-slate-300 text-slate-700 focus:ring-0"
          />
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-xs bg-slate-400/40 border border-slate-600 inline-block" />
            Cadastral Fabric
          </span>
        </label>

        {onToggleLayer && (
          <>
            <label className="flex items-center gap-1.5 cursor-pointer hover:text-blue-800">
              <input
                type="checkbox"
                checked={showLegacy}
                onChange={() => onToggleLayer('legacy')}
                className="rounded border-slate-300 text-blue-700 focus:ring-0"
              />
              <span className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-xs bg-blue-600/30 border border-blue-700 inline-block" />
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
                <span className="w-2.5 h-2.5 rounded-xs bg-amber-500/30 border border-amber-600 inline-block" />
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
                <span className="w-2.5 h-2.5 rounded-xs bg-emerald-500/40 border border-emerald-700 inline-block" />
                Reconciled
              </span>
            </label>
          </>
        )}
      </div>

      {/* Navigation Quick Actions (Fit Fabric / Fit Selected) */}
      <div className="absolute top-14 left-3 z-[1000] flex flex-col gap-1.5">
        {fabricBounds && (
          <button
            onClick={fitFabric}
            title="Zoom to Entire Cadastral Fabric"
            className="p-1.5 bg-white/95 hover:bg-white text-slate-700 hover:text-slate-900 border border-slate-300 rounded shadow-xs text-xs flex items-center gap-1 cursor-pointer"
          >
            <Maximize2 className="w-3.5 h-3.5 text-blue-600" />
            <span className="text-[11px] font-medium pr-1">Fit All</span>
          </button>
        )}
        {selectedBounds && (
          <button
            onClick={fitSelected}
            title="Zoom to Selected Parcel"
            className="p-1.5 bg-white/95 hover:bg-white text-slate-700 hover:text-slate-900 border border-slate-300 rounded shadow-xs text-xs flex items-center gap-1 cursor-pointer"
          >
            <Crosshair className="w-3.5 h-3.5 text-emerald-600" />
            <span className="text-[11px] font-medium pr-1">Focus Parcel</span>
          </button>
        )}
      </div>

      {/* Coordinate / CRS Badge */}
      <div className="absolute bottom-2 left-3 z-[1000] bg-white/90 text-[10px] text-slate-500 px-2 py-0.5 rounded border border-slate-200 shadow-2xs">
        Leaflet WebGIS Fabric | CRS: EPSG:4326 / Projected EPSG:32643 | OpenStreetMap
      </div>
    </div>
  );
};
