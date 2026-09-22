import { useEffect, useRef, useState } from 'react';
import { Map, NavigationControl, LngLatBounds } from 'maplibre-gl';
import type { GeoJSONSource } from 'maplibre-gl';
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
  const mapRef = useRef<Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Initialize MapLibre
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    const map = new Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          'carto-positron': {
            type: 'raster',
            tiles: [
              'https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
              'https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png'
            ],
            tileSize: 256,
            attribution: '&copy; CartoDB, OpenStreetMap contributors'
          }
        },
        layers: [
          {
            id: 'carto-basemap',
            type: 'raster',
            source: 'carto-positron',
            minzoom: 0,
            maxzoom: 19
          }
        ]
      },
      center: [73.7380, 18.5910], // Default Pune / Hinjewadi demo area
      zoom: 16.5,
      pitch: 0,
      bearing: 0
    });

    map.addControl(new NavigationControl({ showCompass: true }), 'top-right');

    map.on('load', () => {
      // 1. Legacy Layer Source
      map.addSource('legacy-source', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });
      map.addLayer({
        id: 'legacy-fill',
        type: 'fill',
        source: 'legacy-source',
        paint: {
          'fill-color': '#3b82f6',
          'fill-opacity': 0.15
        }
      });
      map.addLayer({
        id: 'legacy-line',
        type: 'line',
        source: 'legacy-source',
        paint: {
          'line-color': '#1d4ed8',
          'line-width': 2,
          'line-dasharray': [3, 2]
        }
      });

      // 2. Drone Layer Source
      map.addSource('drone-source', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });
      map.addLayer({
        id: 'drone-fill',
        type: 'fill',
        source: 'drone-source',
        paint: {
          'fill-color': '#f59e0b',
          'fill-opacity': 0.18
        }
      });
      map.addLayer({
        id: 'drone-line',
        type: 'line',
        source: 'drone-source',
        paint: {
          'line-color': '#d97706',
          'line-width': 2.5
        }
      });

      // 3. Reconciled Layer Source
      map.addSource('reconciled-source', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });
      map.addLayer({
        id: 'reconciled-fill',
        type: 'fill',
        source: 'reconciled-source',
        paint: {
          'fill-color': '#10b981',
          'fill-opacity': 0.25
        }
      });
      map.addLayer({
        id: 'reconciled-line',
        type: 'line',
        source: 'reconciled-source',
        paint: {
          'line-color': '#059669',
          'line-width': 3
        }
      });

      // 4. GNSS Points Layer Source
      map.addSource('gnss-source', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });
      map.addLayer({
        id: 'gnss-circle',
        type: 'circle',
        source: 'gnss-source',
        paint: {
          'circle-radius': 5,
          'circle-color': '#ef4444',
          'circle-stroke-width': 1.5,
          'circle-stroke-color': '#ffffff'
        }
      });

      setMapLoaded(true);
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update GeoJSON layers when selected parcel changes
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    const map = mapRef.current;

    // Legacy feature
    const legacySource = map.getSource('legacy-source') as GeoJSONSource;
    if (legacySource && selectedParcel?.geometry_geojson) {
      legacySource.setData({
        type: 'FeatureCollection',
        features: [
          {
            type: 'Feature',
            properties: { id: selectedParcel.parcel_id, survey: selectedParcel.full_survey },
            geometry: selectedParcel.geometry_geojson
          }
        ]
      });
    }

    // Drone feature
    const droneSource = map.getSource('drone-source') as GeoJSONSource;
    if (droneSource) {
      if (selectedParcel?.drone_geometry_geojson) {
        droneSource.setData({
          type: 'FeatureCollection',
          features: [
            {
              type: 'Feature',
              properties: { candidate: selectedParcel.full_survey },
              geometry: selectedParcel.drone_geometry_geojson
            }
          ]
        });
      } else {
        droneSource.setData({ type: 'FeatureCollection', features: [] });
      }
    }

    // Reconciled feature
    const reconciledSource = map.getSource('reconciled-source') as GeoJSONSource;
    if (reconciledSource) {
      if (selectedParcel?.reconciled_geometry_geojson) {
        reconciledSource.setData({
          type: 'FeatureCollection',
          features: [
            {
              type: 'Feature',
              properties: { reconciled: true },
              geometry: selectedParcel.reconciled_geometry_geojson
            }
          ]
        });
      } else {
        reconciledSource.setData({ type: 'FeatureCollection', features: [] });
      }
    }

    // GNSS points
    const gnssSource = map.getSource('gnss-source') as GeoJSONSource;
    if (gnssSource) {
      if (selectedParcel?.gnss_points && selectedParcel.gnss_points.length > 0) {
        gnssSource.setData({
          type: 'FeatureCollection',
          features: selectedParcel.gnss_points.map((pt) => ({
            type: 'Feature',
            properties: { id: pt.point_id, accuracy: pt.accuracy_m },
            geometry: {
              type: 'Point',
              coordinates: [pt.longitude, pt.latitude]
            }
          }))
        });
      } else {
        gnssSource.setData({ type: 'FeatureCollection', features: [] });
      }
    }

    // Fit bounds to selected parcel
    if (selectedParcel?.geometry_geojson?.coordinates) {
      try {
        const coords = selectedParcel.geometry_geojson.coordinates[0];
        const bounds = new LngLatBounds();
        coords.forEach((coord: [number, number]) => {
          bounds.extend(coord);
        });
        map.fitBounds(bounds, { padding: 80, maxZoom: 18.5, duration: 600 });
      } catch (e) {
        // Fallback
      }
    }
  }, [selectedParcel, mapLoaded]);

  // Update visibility according to layer toggles
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    const map = mapRef.current;

    const setVisibility = (layerId: string, visible: boolean) => {
      if (map.getLayer(layerId)) {
        map.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none');
      }
    };

    setVisibility('legacy-fill', showLegacy);
    setVisibility('legacy-line', showLegacy);
    setVisibility('drone-fill', showDrone);
    setVisibility('drone-line', showDrone);
    setVisibility('reconciled-fill', showReconciled);
    setVisibility('reconciled-line', showReconciled);
    setVisibility('gnss-circle', showGnss);
  }, [showLegacy, showDrone, showGnss, showReconciled, mapLoaded]);

  return (
    <div className="relative w-full h-full min-h-[420px] bg-slate-100 overflow-hidden border border-slate-200">
      <div ref={mapContainer} className="w-full h-full absolute inset-0" />

      {/* Layer Control Bar: Only Legacy, Drone, GNSS, Reconciled */}
      {onToggleLayer && (
        <div className="absolute top-3 left-3 z-10 bg-white/95 backdrop-blur-sm border border-slate-300 shadow-sm rounded px-3 py-2 flex items-center gap-4 text-xs font-medium text-slate-700 select-none">
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
      <div className="absolute bottom-2 left-3 z-10 bg-white/90 text-[10px] text-slate-500 px-2 py-0.5 rounded border border-slate-200">
        CRS: EPSG:4326 (WGS 84) | Precision Survey Engine
      </div>
    </div>
  );
};
