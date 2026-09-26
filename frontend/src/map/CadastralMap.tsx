import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import type { ParcelDetail } from '../types/cadastral';
import type { CanonicalBuilding } from '../types/canonical';
import { getParcelsGeoJSON, getCanonicalBuildings } from '../services/api';
import { Maximize2, Crosshair, Wrench, AlertTriangle, Eye, Sparkles } from 'lucide-react';

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

const GOOGLE_MAPS_API_KEY = (import.meta as any).env?.VITE_GOOGLE_MAPS_API_KEY || '';

const BASEMAP_OPTIONS = {
  'google-hybrid': {
    name: 'Google Hybrid (Satellite + Labels)',
    url: GOOGLE_MAPS_API_KEY
      ? `https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}&key=${GOOGLE_MAPS_API_KEY}`
      : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; Google Maps / OSM'
  },
  'google-satellite': {
    name: 'Google Satellite (Aerial)',
    url: GOOGLE_MAPS_API_KEY
      ? `https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}&key=${GOOGLE_MAPS_API_KEY}`
      : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; Google Maps / OSM'
  },
  'google-streets': {
    name: 'Google Streets',
    url: GOOGLE_MAPS_API_KEY
      ? `https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}&key=${GOOGLE_MAPS_API_KEY}`
      : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; Google Maps / OSM'
  },
  'osm': {
    name: 'OpenStreetMap',
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; OpenStreetMap'
  },
  'offline-grid': {
    name: 'Offline Neutral Basemap (Local Canvas)',
    url: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256"><rect width="256" height="256" fill="%23f1f5f9"/><path d="M0 64 H256 M0 128 H256 M0 192 H256 M64 0 V256 M128 0 V256 M192 0 V256" stroke="%23e2e8f0" stroke-width="1"/></svg>',
    attribution: 'Local Offline Grid'
  }
};

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
  const basemapTileRef = useRef<L.TileLayer | null>(null);

  const [activeBasemap, setActiveBasemap] = useState<keyof typeof BASEMAP_OPTIONS>('google-hybrid');
  const [showFabric, setShowFabric] = useState(true);
  const [showBuildings, setShowBuildings] = useState(true);
  const [showOriRaster, setShowOriRaster] = useState(false);
  const [oriOpacity, setOriOpacity] = useState(0.85);
  const [fabricBounds, setFabricBounds] = useState<L.LatLngBounds | null>(null);
  const [selectedBounds, setSelectedBounds] = useState<L.LatLngBounds | null>(null);

  // Buildings state
  const [buildings, setBuildings] = useState<CanonicalBuilding[]>([]);

  // Developer Geometry Debug mode toggles
  const [geometryDebug, setGeometryDebug] = useState(false);
  const [debugShowBbox, setDebugShowBbox] = useState(true);
  const [debugShowMask, setDebugShowMask] = useState(true);
  const [debugShowCentroids, setDebugShowCentroids] = useState(true);
  const [debugShowVertices, setDebugShowVertices] = useState(false);

  // Active inspected geometry metadata
  const [inspectedEntity, setInspectedEntity] = useState<{
    type: 'Parcel' | 'Building';
    id: string;
    survey?: string;
    area_m2: number;
    vertex_count: number;
    geom_type: string;
    centroid: [number, number];
    crs: string;
    conf?: number;
    status?: string;
    bounds?: [number, number, number, number];
    pixel_bbox?: [number, number, number, number];
  } | null>(null);

  // Layer groups for dynamic toggling & updates
  const oriOverlayRef = useRef<L.ImageOverlay | null>(null);

  // Layer groups for dynamic toggling & updates
  const fabricLayerGroup = useRef<L.LayerGroup>(L.layerGroup());
  const legacyLayerGroup = useRef<L.LayerGroup>(L.layerGroup());
  const droneLayerGroup = useRef<L.LayerGroup>(L.layerGroup());
  const gnssLayerGroup = useRef<L.LayerGroup>(L.layerGroup());
  const reconciledLayerGroup = useRef<L.LayerGroup>(L.layerGroup());
  const buildingsLayerGroup = useRef<L.LayerGroup>(L.layerGroup());
  const debugLayerGroup = useRef<L.LayerGroup>(L.layerGroup());

  // Keep a ref to onSelectParcelId to avoid recreating layers when callback changes
  const onSelectRef = useRef(onSelectParcelId);
  useEffect(() => {
    onSelectRef.current = onSelectParcelId;
  }, [onSelectParcelId]);

  // Handle dynamic basemap changes
  useEffect(() => {
    if (!mapRef.current) return;
    if (basemapTileRef.current) {
      mapRef.current.removeLayer(basemapTileRef.current);
    }
    const option = BASEMAP_OPTIONS[activeBasemap];
    const newTileLayer = L.tileLayer(option.url, {
      maxZoom: 21,
      attribution: option.attribution
    });
    newTileLayer.addTo(mapRef.current);
    basemapTileRef.current = newTileLayer;
  }, [activeBasemap]);

  // 1. Initialize Leaflet Map
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    // Centered around Coimbatore Corporation, Tamil Nadu (EPSG:4326)
    const map = L.map(mapContainer.current, {
      center: [11.0050, 76.9550],
      zoom: 17,
      zoomControl: false
    });

    L.control.zoom({ position: 'topright' }).addTo(map);

    // Initial Google Maps Hybrid Tile Layer
    const initialOption = BASEMAP_OPTIONS['google-hybrid'];
    const initialTile = L.tileLayer(initialOption.url, {
      maxZoom: 21,
      attribution: initialOption.attribution
    }).addTo(map);
    basemapTileRef.current = initialTile;

    // Add layer groups to map in rendering order
    fabricLayerGroup.current.addTo(map);
    buildingsLayerGroup.current.addTo(map);
    legacyLayerGroup.current.addTo(map);
    droneLayerGroup.current.addTo(map);
    gnssLayerGroup.current.addTo(map);
    reconciledLayerGroup.current.addTo(map);
    debugLayerGroup.current.addTo(map);

    mapRef.current = map;

    // 2. Fetch Full Cadastral Fabric GeoJSON (Authentic irregular polygons)
    getParcelsGeoJSON()
      .then((geojson) => {
        if (!mapRef.current) return;
        fabricLayerGroup.current.clearLayers();

        const geoJsonLayer = L.geoJSON(geojson, {
          style: (feature) => {
            const isConflict = feature?.properties?.status === 'Conflict';
            return {
              color: isConflict ? '#d97706' : '#475569',
              weight: isConflict ? 2 : 1.2,
              dashArray: isConflict ? '4, 4' : undefined,
              fillColor: isConflict ? '#fef3c7' : '#94a3b8',
              fillOpacity: isConflict ? 0.35 : 0.15
            };
          },
          onEachFeature: (feature, layer) => {
            if (feature.properties) {
              const pId = feature.properties.parcel_id;
              const sNo = feature.properties.full_survey || feature.properties.survey_no;
              const status = feature.properties.status;
              const conf = (feature.properties.confidence || 0).toFixed(1);
              const area = feature.properties.legacy_area || 0;
              const vCount = feature.properties.vertex_count || 8;
              const centroid = feature.properties.centroid || [11.005, 76.955];

              layer.bindTooltip(
                `<div class="font-sans text-xs">
                  <b class="text-slate-900">Parcel ${pId} (Survey ${sNo})</b><br/>
                  Area: <b>${area.toLocaleString()} m²</b> | Vertices: <b>${vCount}</b><br/>
                  Centroid: <span class="font-mono text-[10px] text-slate-500">${centroid[1].toFixed(5)}, ${centroid[0].toFixed(5)}</span><br/>
                  Status: <span class="${status === 'Conflict' ? 'text-amber-600 font-bold' : 'text-emerald-600 font-bold'}">${status}</span><br/>
                  Confidence: <b>${conf}%</b>
                </div>`,
                { sticky: true }
              );

              layer.on('click', () => {
                setInspectedEntity({
                  type: 'Parcel',
                  id: pId,
                  survey: sNo,
                  area_m2: area,
                  vertex_count: vCount,
                  geom_type: feature.geometry?.type || 'Polygon',
                  centroid: [centroid[1], centroid[0]],
                  crs: 'EPSG:4326',
                  conf: parseFloat(conf),
                  status: status
                });

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
      .catch((err) => console.error('Failed to load authentic parcel fabric:', err));

    // 3. Fetch Real AI Buildings (YOLOv8-Seg ONNX extractions)
    getCanonicalBuildings()
      .then((blds) => {
        setBuildings(blds);
      })
      .catch((err) => console.error('Failed to load YOLOv8 buildings:', err));

    return () => {
      if (oriOverlayRef.current && mapRef.current) {
        mapRef.current.removeLayer(oriOverlayRef.current);
        oriOverlayRef.current = null;
      }
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Handle Drone ORI Raster ImageOverlay
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (oriOverlayRef.current) {
      map.removeLayer(oriOverlayRef.current);
      oriOverlayRef.current = null;
    }

    if (showOriRaster) {
      // True bounds of the drone ORI GeoTIFF: [[11.0000, 76.9500], [11.0064, 76.9564]]
      const bounds: L.LatLngBoundsExpression = [[11.0000, 76.9500], [11.0064, 76.9564]];
      const overlay = L.imageOverlay('/api/raster/ori-overlay', bounds, {
        opacity: oriOpacity,
        interactive: false
      });
      overlay.addTo(map);
      oriOverlayRef.current = overlay;
    }
  }, [showOriRaster, oriOpacity]);

  // 3. Render AI Buildings Layer (YOLOv8-Seg Multi-Vertex Polygons)
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    buildingsLayerGroup.current.clearLayers();

    if (!showBuildings || buildings.length === 0) return;

    buildings.forEach((b) => {
      if (!b.geometry_geojson) return;

      const isConflict = b.conflict_status === 'BOUNDARY_CONFLICT';
      const isSBI = b.building_id === 'BLD-SBI-0001' || b.building_type?.includes('State Bank of India');
      
      const bLayer = L.geoJSON(b.geometry_geojson, {
        style: {
          color: isSBI ? '#dc2626' : (isConflict ? '#d97706' : '#7c3aed'),
          weight: isSBI ? 3.0 : 2,
          fillColor: isSBI ? '#ef4444' : (isConflict ? '#f59e0b' : '#a78bfa'),
          fillOpacity: isSBI ? 0.40 : 0.55
        },
        onEachFeature: (_, layer) => {
          layer.bindTooltip(
            `<div class="font-sans text-xs">
              <b class="${isSBI ? 'text-red-700 font-extrabold text-sm' : 'text-purple-800'}">${b.building_id}</b><br/>
              <span class="${isSBI ? 'text-red-900 font-bold' : 'text-slate-700'}">${b.building_type}</span><br/>
              Model: <span class="font-mono text-purple-700 font-bold">${b.model_version}</span><br/>
              Area: <b>${b.area_m2.toLocaleString()} m²</b> | Vertices: <b>${b.vertex_count || 6}</b><br/>
              Confidence: <b>${b.confidence.toFixed(1)}%</b><br/>
              Parcel: <b>${b.parcel_uid || 'P001'} (Survey ${b.survey_number || '200/1'})</b><br/>
              Status: <span class="${isSBI ? 'text-red-600 font-bold' : (isConflict ? 'text-amber-700 font-bold' : 'text-emerald-700 font-bold')}">${isSBI ? 'Real Building Footprint (SBI Complex)' : (isConflict ? `Boundary Cross (${(100 - (b.overlap_percentage || 100)).toFixed(1)}% outside)` : 'Within Parcel')}</span>
            </div>`,
            { sticky: true }
          );

          layer.on('click', (e) => {
            L.DomEvent.stopPropagation(e);
            setInspectedEntity({
              type: 'Building',
              id: b.building_id,
              survey: b.survey_number,
              area_m2: b.area_m2,
              vertex_count: b.vertex_count || 8,
              geom_type: b.geometry_geojson?.type || 'Polygon',
              centroid: b.centroid || [11.005, 76.955],
              crs: b.crs || 'EPSG:4326',
              conf: b.confidence,
              status: b.conflict_status,
              bounds: b.bbox,
              pixel_bbox: b.pixel_bbox
            });
          });
        }
      });

      buildingsLayerGroup.current.addLayer(bLayer);
    });
  }, [showBuildings, buildings]);

  // 4. Update Selected Parcel Geometries & Conflict Highlights
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    legacyLayerGroup.current.clearLayers();
    droneLayerGroup.current.clearLayers();
    gnssLayerGroup.current.clearLayers();
    reconciledLayerGroup.current.clearLayers();

    if (!selectedParcel) {
      setSelectedBounds(null);
      return;
    }

    const bounds = L.latLngBounds([]);

    // 1. Legacy Geometry (Blue dashed stroke)
    if (selectedParcel.geometry_geojson) {
      const legacyGeo = L.geoJSON(selectedParcel.geometry_geojson, {
        style: {
          color: '#1d4ed8',
          weight: 2.8,
          dashArray: '5, 5',
          fillColor: '#3b82f6',
          fillOpacity: 0.22
        }
      });
      legacyLayerGroup.current.addLayer(legacyGeo);
      try {
        bounds.extend(legacyGeo.getBounds());
      } catch (e) {}
    }

    // 2. Drone Geometry (Amber solid stroke)
    if (selectedParcel.drone_geometry_geojson) {
      const droneGeo = L.geoJSON(selectedParcel.drone_geometry_geojson, {
        style: {
          color: '#d97706',
          weight: 3.2,
          fillColor: '#f59e0b',
          fillOpacity: 0.28
        }
      });
      droneLayerGroup.current.addLayer(droneGeo);
      try {
        bounds.extend(droneGeo.getBounds());
      } catch (e) {}
    }

    // 3. Reconciled Geometry (Emerald Green authoritative stroke)
    if (selectedParcel.reconciled_geometry_geojson) {
      const recGeo = L.geoJSON(selectedParcel.reconciled_geometry_geojson, {
        style: {
          color: '#059669',
          weight: 3.8,
          fillColor: '#10b981',
          fillOpacity: 0.32
        }
      });
      reconciledLayerGroup.current.addLayer(recGeo);
      try {
        bounds.extend(recGeo.getBounds());
      } catch (e) {}
    }

    // 4. GNSS Points (High-precision CORS markers)
    if (selectedParcel.gnss_points && selectedParcel.gnss_points.length > 0) {
      selectedParcel.gnss_points.forEach((pt) => {
        const marker = L.circleMarker([pt.latitude, pt.longitude], {
          radius: 5,
          fillColor: '#ef4444',
          color: '#ffffff',
          weight: 2,
          fillOpacity: 0.95
        });
        marker.bindPopup(`<b>GNSS/RTK Point:</b> ${pt.point_id}<br/><b>Accuracy:</b> ±${pt.accuracy_m}m`);
        gnssLayerGroup.current.addLayer(marker);
        bounds.extend([pt.latitude, pt.longitude]);
      });
    }

    if (bounds.isValid()) {
      setSelectedBounds(bounds);
      map.fitBounds(bounds, { padding: [60, 60], maxZoom: 19 });
    }
  }, [selectedParcel]);

  // 5. Geometry Debug Mode Overlays
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    debugLayerGroup.current.clearLayers();

    if (!geometryDebug) return;

    // Render debug overlays across buildings and selected parcel
    buildings.forEach((b) => {
      // 1. Show YOLO Bounding Box (dashed yellow)
      if (debugShowBbox && b.bbox_geojson) {
        const bboxLayer = L.geoJSON(b.bbox_geojson, {
          style: {
            color: '#eab308',
            weight: 1.5,
            dashArray: '4, 4',
            fillColor: '#fef08a',
            fillOpacity: 0.08
          }
        });
        debugLayerGroup.current.addLayer(bboxLayer);
      }

      // 2. Show Segmentation Mask (cyan outline)
      if (debugShowMask && b.segmentation_mask_geojson) {
        const maskLayer = L.geoJSON(b.segmentation_mask_geojson, {
          style: {
            color: '#06b6d4',
            weight: 1.8,
            fillColor: '#67e8f9',
            fillOpacity: 0.15
          }
        });
        debugLayerGroup.current.addLayer(maskLayer);
      }

      // 3. Show Centroids (red target markers)
      if (debugShowCentroids && b.centroid) {
        const cMarker = L.circleMarker([b.centroid[1], b.centroid[0]], {
          radius: 4,
          fillColor: '#ef4444',
          color: '#ffffff',
          weight: 1.5,
          fillOpacity: 1
        });
        cMarker.bindTooltip(`<span class="font-mono text-[10px]">${b.building_id} Centroid</span>`);
        debugLayerGroup.current.addLayer(cMarker);
      }

      // 4. Show Polygon Vertices (indigo dots)
      if (debugShowVertices && b.geometry_geojson?.coordinates) {
        const ring = b.geometry_geojson.coordinates[0];
        if (Array.isArray(ring)) {
          ring.forEach((coord: number[]) => {
            const vMarker = L.circleMarker([coord[1], coord[0]], {
              radius: 3,
              fillColor: '#4f46e5',
              color: '#ffffff',
              weight: 1,
              fillOpacity: 0.9
            });
            debugLayerGroup.current.addLayer(vMarker);
          });
        }
      }
    });
  }, [geometryDebug, debugShowBbox, debugShowMask, debugShowCentroids, debugShowVertices, buildings]);

  // 6. Handle Layer Visibility Toggles
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (showFabric) {
      if (!map.hasLayer(fabricLayerGroup.current)) fabricLayerGroup.current.addTo(map);
    } else {
      if (map.hasLayer(fabricLayerGroup.current)) map.removeLayer(fabricLayerGroup.current);
    }

    if (showBuildings) {
      if (!map.hasLayer(buildingsLayerGroup.current)) buildingsLayerGroup.current.addTo(map);
    } else {
      if (map.hasLayer(buildingsLayerGroup.current)) map.removeLayer(buildingsLayerGroup.current);
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
  }, [showFabric, showBuildings, showLegacy, showDrone, showGnss, showReconciled]);

  const fitFabric = () => {
    if (mapRef.current && fabricBounds && fabricBounds.isValid()) {
      mapRef.current.fitBounds(fabricBounds, { padding: [30, 30] });
    }
  };

  const fitSelected = () => {
    if (mapRef.current && selectedBounds && selectedBounds.isValid()) {
      mapRef.current.fitBounds(selectedBounds, { padding: [60, 60], maxZoom: 19 });
    }
  };

  return (
    <div className="relative w-full h-full min-h-[480px] bg-slate-100 overflow-hidden border border-slate-200">
      <div ref={mapContainer} className="w-full h-full absolute inset-0 z-0" />

      {/* Primary Layer Control Bar */}
      <div className="absolute top-3 left-3 z-[1000] bg-white/95 backdrop-blur-xs border border-slate-300 shadow-md rounded-lg px-3 py-2 flex flex-wrap items-center gap-3.5 text-xs font-medium text-slate-700 select-none">
        <span className="text-slate-400 uppercase tracking-wider text-[10px] font-bold mr-0.5">Layers:</span>

        {/* Full Fabric Toggle */}
        <label className="flex items-center gap-1.5 cursor-pointer hover:text-slate-900">
          <input
            type="checkbox"
            checked={showFabric}
            onChange={(e) => setShowFabric(e.target.checked)}
            className="rounded border-slate-300 text-slate-700 focus:ring-0 cursor-pointer"
          />
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-xs bg-slate-400/50 border border-slate-700 inline-block" />
            Cadastral Fabric
          </span>
        </label>

        {/* AI Buildings (YOLOv8-Seg) */}
        <label className="flex items-center gap-1.5 cursor-pointer hover:text-purple-900">
          <input
            type="checkbox"
            checked={showBuildings}
            onChange={(e) => setShowBuildings(e.target.checked)}
            className="rounded border-purple-300 text-purple-600 focus:ring-0 cursor-pointer"
          />
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-xs bg-purple-500/60 border border-purple-800 inline-block" />
            AI Buildings ({buildings.length})
          </span>
        </label>

        {/* Drone ORI Imagery Layer Toggle */}
        <div className="flex items-center gap-1.5 pl-1 border-l border-slate-200">
          <label className="flex items-center gap-1.5 cursor-pointer hover:text-emerald-900">
            <input
              type="checkbox"
              checked={showOriRaster}
              onChange={(e) => setShowOriRaster(e.target.checked)}
              className="rounded border-emerald-400 text-emerald-600 focus:ring-0 cursor-pointer"
            />
            <span className="flex items-center gap-1 font-semibold text-emerald-800">
              <span className="w-2.5 h-2.5 rounded-xs bg-emerald-600 inline-block" />
              Drone ORI Imagery
            </span>
          </label>
          {showOriRaster && (
            <div className="flex items-center gap-1 ml-1">
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.05"
                value={oriOpacity}
                onChange={(e) => setOriOpacity(parseFloat(e.target.value))}
                className="w-14 h-1 bg-slate-200 rounded cursor-pointer accent-emerald-600"
                title={`ORI Opacity: ${Math.round(oriOpacity * 100)}%`}
              />
              <span className="text-[10px] font-mono text-slate-500">{Math.round(oriOpacity * 100)}%</span>
            </div>
          )}
        </div>

        {onToggleLayer && (
          <>
            <label className="flex items-center gap-1.5 cursor-pointer hover:text-blue-800">
              <input
                type="checkbox"
                checked={showLegacy}
                onChange={() => onToggleLayer('legacy')}
                className="rounded border-slate-300 text-blue-700 focus:ring-0 cursor-pointer"
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
                className="rounded border-slate-300 text-amber-600 focus:ring-0 cursor-pointer"
              />
              <span className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-xs bg-amber-500/40 border border-amber-600 inline-block" />
                Drone
              </span>
            </label>

            <label className="flex items-center gap-1.5 cursor-pointer hover:text-red-800">
              <input
                type="checkbox"
                checked={showGnss}
                onChange={() => onToggleLayer('gnss')}
                className="rounded border-slate-300 text-red-600 focus:ring-0 cursor-pointer"
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
                className="rounded border-slate-300 text-emerald-600 focus:ring-0 cursor-pointer"
              />
              <span className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-xs bg-emerald-500/50 border border-emerald-700 inline-block" />
                Reconciled
              </span>
            </label>
          </>
        )}

        {/* Basemap Selector */}
        <div className="flex items-center gap-1.5 border-l border-slate-200 pl-3">
          <span className="text-slate-400 text-[10px] uppercase font-semibold">Basemap:</span>
          <select
            value={activeBasemap}
            onChange={(e) => setActiveBasemap(e.target.value as any)}
            className="bg-slate-50 border border-slate-300 text-slate-800 text-xs rounded px-2 py-0.5 focus:outline-none font-medium cursor-pointer"
          >
            {Object.entries(BASEMAP_OPTIONS).map(([key, opt]) => (
              <option key={key} value={key}>
                {opt.name}
              </option>
            ))}
          </select>
        </div>

        {/* Developer GEOMETRY DEBUG Toggle */}
        <div className="flex items-center gap-1.5 border-l border-slate-200 pl-3">
          <button
            onClick={() => setGeometryDebug(!geometryDebug)}
            className={`px-2.5 py-0.5 rounded text-[11px] font-bold flex items-center gap-1 transition-all cursor-pointer ${
              geometryDebug
                ? 'bg-purple-600 text-white shadow-xs'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-600 border border-slate-300'
            }`}
          >
            <Wrench className="w-3 h-3" />
            <span>GEOMETRY DEBUG</span>
          </button>
        </div>
      </div>

      {/* Sub-debug Controls Bar (Visible when GEOMETRY DEBUG is ON) */}
      {geometryDebug && (
        <div className="absolute top-14 left-3 z-[1000] bg-slate-900/90 text-white backdrop-blur-md border border-purple-500/40 shadow-lg rounded-lg px-3 py-1.5 flex items-center gap-3.5 text-[11px] font-mono">
          <span className="text-purple-300 font-bold flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-purple-400" />
            DEBUG OVERLAYS:
          </span>

          <label className="flex items-center gap-1 cursor-pointer hover:text-yellow-300">
            <input
              type="checkbox"
              checked={debugShowBbox}
              onChange={(e) => setDebugShowBbox(e.target.checked)}
              className="rounded text-yellow-500 focus:ring-0 cursor-pointer"
            />
            <span>YOLO BBox</span>
          </label>

          <label className="flex items-center gap-1 cursor-pointer hover:text-cyan-300">
            <input
              type="checkbox"
              checked={debugShowMask}
              onChange={(e) => setDebugShowMask(e.target.checked)}
              className="rounded text-cyan-500 focus:ring-0 cursor-pointer"
            />
            <span>Mask Contour</span>
          </label>

          <label className="flex items-center gap-1 cursor-pointer hover:text-red-300">
            <input
              type="checkbox"
              checked={debugShowCentroids}
              onChange={(e) => setDebugShowCentroids(e.target.checked)}
              className="rounded text-red-500 focus:ring-0 cursor-pointer"
            />
            <span>Centroids</span>
          </label>

          <label className="flex items-center gap-1 cursor-pointer hover:text-indigo-300">
            <input
              type="checkbox"
              checked={debugShowVertices}
              onChange={(e) => setDebugShowVertices(e.target.checked)}
              className="rounded text-indigo-500 focus:ring-0 cursor-pointer"
            />
            <span>Vertex Nodes</span>
          </label>
        </div>
      )}

      {/* Navigation Quick Actions (Fit Fabric / Fit Selected) */}
      <div className={`absolute left-3 z-[1000] flex flex-col gap-1.5 transition-all ${geometryDebug ? 'top-24' : 'top-14'}`}>
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

      {/* Floating GEOMETRY DEBUG INSPECTOR PANEL (Bottom-Right) */}
      {inspectedEntity && (
        <div className="absolute bottom-10 right-3 z-[1000] w-80 bg-white/95 backdrop-blur-md border border-slate-300 rounded-lg shadow-xl p-3 text-xs">
          <div className="flex items-center justify-between border-b border-slate-200 pb-1.5 mb-2">
            <div className="flex items-center gap-1.5 font-bold text-slate-900">
              <Eye className="w-3.5 h-3.5 text-purple-600" />
              <span>Geometry Inspector ({inspectedEntity.type})</span>
            </div>
            <button
              onClick={() => setInspectedEntity(null)}
              className="text-slate-400 hover:text-slate-600 text-sm font-bold leading-none cursor-pointer"
            >
              &times;
            </button>
          </div>

          <div className="space-y-1.5 font-mono text-[11px]">
            <div className="flex justify-between">
              <span className="text-slate-500">ID:</span>
              <span className="font-bold text-purple-700">{inspectedEntity.id}</span>
            </div>
            {inspectedEntity.survey && (
              <div className="flex justify-between">
                <span className="text-slate-500">Survey No:</span>
                <span className="font-semibold text-slate-800">{inspectedEntity.survey}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-slate-500">Geometry Type:</span>
              <span className="text-slate-700">{inspectedEntity.geom_type}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Vertex Count:</span>
              <span className="font-bold text-slate-900 bg-slate-100 px-1.5 py-0.2 rounded">
                {inspectedEntity.vertex_count} vertices
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">True Geodesic Area:</span>
              <span className="font-bold text-emerald-700">{inspectedEntity.area_m2.toLocaleString()} m²</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Centroid:</span>
              <span className="text-slate-700 text-[10px]">
                {inspectedEntity.centroid[0].toFixed(6)}°E, {inspectedEntity.centroid[1].toFixed(6)}°N
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Source CRS:</span>
              <span className="text-blue-700 font-semibold">{inspectedEntity.crs}</span>
            </div>
            {inspectedEntity.conf !== undefined && (
              <div className="flex justify-between">
                <span className="text-slate-500">Confidence:</span>
                <span className="font-bold text-slate-900">{inspectedEntity.conf.toFixed(1)}%</span>
              </div>
            )}
            {inspectedEntity.status && (
              <div className="flex justify-between items-center pt-1 border-t border-slate-100">
                <span className="text-slate-500">Status:</span>
                <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                  inspectedEntity.status === 'Conflict' || inspectedEntity.status === 'BOUNDARY_CONFLICT'
                    ? 'bg-amber-100 text-amber-800'
                    : 'bg-emerald-100 text-emerald-800'
                }`}>
                  {inspectedEntity.status}
                </span>
              </div>
            )}

            {inspectedEntity.type === 'Building' && (
              <div className="pt-2 border-t border-slate-100 space-y-1.5">
                {inspectedEntity.pixel_bbox && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Pixel BBox:</span>
                    <span className="font-mono text-slate-800 bg-slate-100 px-1 py-0.2 rounded text-[10px]">
                      [{inspectedEntity.pixel_bbox.join(', ')}]
                    </span>
                  </div>
                )}
                {inspectedEntity.bounds && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Geo BBox:</span>
                    <span className="font-mono text-slate-800 text-[10px]">
                      [{inspectedEntity.bounds.map((v) => v.toFixed(5)).join(', ')}]
                    </span>
                  </div>
                )}
                <button
                  onClick={() => {
                    setShowOriRaster(true);
                    if (mapRef.current && inspectedEntity.centroid) {
                      mapRef.current.setView([inspectedEntity.centroid[1], inspectedEntity.centroid[0]], 19);
                    }
                  }}
                  className="w-full mt-2 py-1 px-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[11px] font-semibold flex items-center justify-center gap-1 shadow-xs cursor-pointer transition-colors"
                >
                  <Eye className="w-3 h-3" />
                  <span>View Source ORI Imagery</span>
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Dedicated CONFLICT VISUALIZATION CARD (Top-Right when a conflict parcel is active) */}
      {selectedParcel && (selectedParcel.status === 'Conflict' || selectedParcel.conflict_type) && (
        <div className="absolute top-3 right-3 z-[1000] w-84 bg-white/95 backdrop-blur-md border-2 border-amber-500/60 rounded-lg shadow-xl p-3 text-xs">
          <div className="flex items-center gap-1.5 text-amber-800 font-bold border-b border-amber-200 pb-1.5 mb-2">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span>Spatial Conflict Audit: Parcel {selectedParcel.parcel_id}</span>
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between font-mono">
              <span className="text-slate-500">Survey Reference:</span>
              <span className="font-bold text-slate-900">{selectedParcel.full_survey}</span>
            </div>
            <div className="flex justify-between font-mono">
              <span className="text-slate-500">Legacy Boundary Area:</span>
              <span className="font-semibold text-blue-700">
                {selectedParcel.sources_comparison?.legacy?.toLocaleString()} m²
              </span>
            </div>
            <div className="flex justify-between font-mono">
              <span className="text-slate-500">Drone Evidence Area:</span>
              <span className="font-semibold text-amber-700">
                {selectedParcel.sources_comparison?.drone?.toLocaleString() || 'N/A'} m²
              </span>
            </div>
            <div className="flex justify-between font-mono">
              <span className="text-slate-500">Reconciled Proposal:</span>
              <span className="font-bold text-emerald-700">
                {selectedParcel.recommendation?.recommended_area?.toLocaleString() || selectedParcel.sources_comparison?.legacy?.toLocaleString() || 'N/A'} m²
              </span>
            </div>

            <div className="p-2 bg-amber-50 border border-amber-200 rounded text-[11px] text-amber-900 leading-snug mt-2">
              <b>Conflict Reason:</b> {selectedParcel.recommendation?.explanation_summary || selectedParcel.conflict_type || 'Discrepancy detected across spatial sources.'}
            </div>

            <div className="flex items-center justify-between pt-1 text-[11px] font-bold">
              <span className="text-slate-600">Action:</span>
              <span className="bg-red-100 text-red-800 px-2 py-0.5 rounded font-mono">
                HUMAN REVIEW REQUIRED
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Coordinate & Spatial Alignment Footer Badge */}
      <div className="absolute bottom-2 left-3 z-[1000] bg-white/90 text-[10px] text-slate-500 px-2 py-0.5 rounded border border-slate-200 shadow-2xs font-mono flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
        <span>Leaflet WebGIS | Real Cadastral Fabric ({buildings.length} AI Footprints) | CRS: EPSG:4326 / Projected EPSG:32643</span>
      </div>
    </div>
  );
};
