import React, { useState, useRef, useEffect } from 'react';
import L from 'leaflet';
import { MoveHorizontal } from 'lucide-react';
import { getParcelsGeoJSON, getCanonicalBuildings } from '../services/api';

interface BeforeAfterSliderProps {
  beforeTitle?: string;
  afterTitle?: string;
  beforeYear?: string;
  afterYear?: string;
}

export const BeforeAfterSlider: React.FC<BeforeAfterSliderProps> = ({
  beforeTitle = 'Historical Cadastral Register',
  afterTitle = 'Current Drone ORI & AI Extracted Footprints',
  beforeYear = '2023',
  afterYear = '2026'
}) => {
  const [sliderPosition, setSliderPosition] = useState(50);
  const isDragging = useRef(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const leftMapContainer = useRef<HTMLDivElement>(null);
  const rightMapContainer = useRef<HTMLDivElement>(null);
  const leftMapRef = useRef<L.Map | null>(null);
  const rightMapRef = useRef<L.Map | null>(null);
  const isSyncing = useRef(false);

  const handleMove = (clientX: number) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    let percentage = (x / rect.width) * 100;
    if (percentage < 5) percentage = 5;
    if (percentage > 95) percentage = 95;
    setSliderPosition(percentage);
  };

  const handleTouchMove = (e: TouchEvent) => {
    if (!isDragging.current) return;
    handleMove(e.touches[0].clientX);
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging.current) return;
    handleMove(e.clientX);
  };

  const handleMouseUp = () => {
    isDragging.current = false;
  };

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    window.addEventListener('touchmove', handleTouchMove);
    window.addEventListener('touchend', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('touchmove', handleTouchMove);
      window.removeEventListener('touchend', handleMouseUp);
    };
  }, []);

  // Initialize Dual Leaflet Maps with Real GIS Data
  useEffect(() => {
    if (!leftMapContainer.current || !rightMapContainer.current) return;
    if (leftMapRef.current || rightMapRef.current) return;

    const initialCenter: [number, number] = [11.0168, 76.9558];
    const initialZoom = 17;

    const googleTileUrl = `https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}&key=AIzaSyDbZrepladZZyc2oaBOLhjumkrUUxaXJEQ`;

    // 1. Left Map: Historical Cadastral (2023)
    const leftMap = L.map(leftMapContainer.current, {
      center: initialCenter,
      zoom: initialZoom,
      zoomControl: false,
      attributionControl: false
    });
    L.tileLayer(googleTileUrl, { maxZoom: 21 }).addTo(leftMap);

    // 2. Right Map: Current Drone & AI Footprints (2026)
    const rightMap = L.map(rightMapContainer.current, {
      center: initialCenter,
      zoom: initialZoom,
      zoomControl: false,
      attributionControl: false
    });
    L.tileLayer(googleTileUrl, { maxZoom: 21 }).addTo(rightMap);

    // Synchronize Maps Pan and Zoom
    const syncMaps = (source: L.Map, target: L.Map) => {
      source.on('move', () => {
        if (isSyncing.current) return;
        isSyncing.current = true;
        target.setView(source.getCenter(), source.getZoom(), { animate: false });
        isSyncing.current = false;
      });
    };
    syncMaps(leftMap, rightMap);
    syncMaps(rightMap, leftMap);

    leftMapRef.current = leftMap;
    rightMapRef.current = rightMap;

    // Load Real Vector Data for Left Map (Historical Cadastral)
    getParcelsGeoJSON()
      .then((geojson) => {
        if (!leftMapRef.current || !rightMapRef.current) return;

        // Render Historical Legacy Polygons on Left Map
        const legacyLayer = L.geoJSON(geojson, {
          style: {
            color: '#1d4ed8',
            weight: 2,
            dashArray: '5, 5',
            fillColor: '#3b82f6',
            fillOpacity: 0.25
          },
          onEachFeature: (feature, layer) => {
            if (feature.properties) {
              layer.bindTooltip(
                `<b>Historical Parcel ${feature.properties.full_survey || feature.properties.survey_no}</b><br/>Area: ${feature.properties.legacy_area_m2} m²`,
                { sticky: true }
              );
            }
          }
        }).addTo(leftMap);

        // Render Drone Boundaries on Right Map
        L.geoJSON(geojson, {
          style: {
            color: '#d97706',
            weight: 2,
            fillColor: '#f59e0b',
            fillOpacity: 0.15
          },
          onEachFeature: (feature, layer) => {
            if (feature.properties) {
              layer.bindTooltip(
                `<b>Drone Cadastral ${feature.properties.full_survey || feature.properties.survey_no}</b><br/>Status: ${feature.properties.status}`,
                { sticky: true }
              );
            }
          }
        }).addTo(rightMap);

        try {
          const bounds = legacyLayer.getBounds();
          if (bounds.isValid()) {
            leftMap.fitBounds(bounds, { padding: [20, 20] });
            rightMap.fitBounds(bounds, { padding: [20, 20] });
          }
        } catch (e) {}
      })
      .catch((err) => console.error('Error loading parcels for slider:', err));

    // Load Real AI Building Footprints for Right Map
    getCanonicalBuildings()
      .then((buildings) => {
        if (!rightMapRef.current) return;
        buildings.forEach((bldg) => {
          if (bldg.geometry_geojson) {
            L.geoJSON(bldg.geometry_geojson as any, {
              style: {
                color: '#7e22ce',
                weight: 1.5,
                fillColor: '#a855f7',
                fillOpacity: 0.6
              },
              onEachFeature: (_, layer) => {
                layer.bindTooltip(
                  `<b>AI Building Footprint</b><br/>ID: ${bldg.building_id}<br/>Area: ${bldg.area_m2.toFixed(1)} m²<br/>Conf: ${(bldg.confidence > 1 ? bldg.confidence : bldg.confidence * 100).toFixed(1)}%`,
                  { sticky: true }
                );
              }
            }).addTo(rightMap);
          }
        });
      })
      .catch((err) => console.error('Error loading AI buildings for slider:', err));

    return () => {
      leftMap.remove();
      rightMap.remove();
      leftMapRef.current = null;
      rightMapRef.current = null;
    };
  }, []);

  return (
    <div className="relative w-full h-[420px] rounded-lg overflow-hidden border border-slate-300 select-none bg-slate-950 font-sans shadow-inner">
      <div
        ref={containerRef}
        className="relative w-full h-full cursor-ew-resize overflow-hidden"
      >
        {/* AFTER Layer (Right / Full Background) */}
        <div className="absolute inset-0 w-full h-full z-10">
          <div ref={rightMapContainer} className="w-full h-full" />
          {/* Right Top Header Badge */}
          <div className="absolute top-3 right-3 z-[1000] bg-emerald-950/85 text-emerald-200 border border-emerald-600/60 px-3 py-1.5 rounded shadow text-xs font-bold tracking-wide flex items-center gap-2 pointer-events-none">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            {afterYear} — {afterTitle}
          </div>
          {/* Right Legend */}
          <div className="absolute bottom-3 right-3 z-[1000] bg-white/90 backdrop-blur-xs border border-slate-300 rounded px-2.5 py-1 text-[11px] text-slate-700 font-medium flex items-center gap-3 shadow-xs pointer-events-none">
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-sm bg-amber-500/30 border border-amber-600 inline-block" /> Drone Boundaries
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-sm bg-purple-500/60 border border-purple-700 inline-block" /> AI Extracted Buildings
            </span>
          </div>
        </div>

        {/* BEFORE Layer (Left / Clipped View) */}
        <div
          className="absolute inset-0 h-full z-20 overflow-hidden border-r-2 border-white shadow-[2px_0_12px_rgba(0,0,0,0.5)]"
          style={{ width: `${sliderPosition}%` }}
        >
          <div
            ref={leftMapContainer}
            className="h-full"
            style={{
              width: containerRef.current ? `${containerRef.current.clientWidth}px` : '100vw'
            }}
          />
          {/* Left Top Header Badge */}
          <div className="absolute top-3 left-3 z-[1000] bg-blue-950/85 text-blue-200 border border-blue-600/60 px-3 py-1.5 rounded shadow text-xs font-bold tracking-wide flex items-center gap-2 pointer-events-none">
            <span className="w-2 h-2 rounded-full bg-blue-400" />
            {beforeYear} — {beforeTitle}
          </div>
          {/* Left Legend */}
          <div className="absolute bottom-3 left-3 z-[1000] bg-white/90 backdrop-blur-xs border border-slate-300 rounded px-2.5 py-1 text-[11px] text-slate-700 font-medium flex items-center gap-2 shadow-xs pointer-events-none">
            <span className="w-2.5 h-2.5 rounded-sm bg-blue-500/30 border border-blue-600 inline-block" /> Historical Cadastral (2023)
          </div>
        </div>

        {/* DRAGGABLE DIVIDER HANDLE */}
        <div
          className="absolute top-0 bottom-0 w-1 bg-white cursor-ew-resize z-30 shadow-[0_0_12px_rgba(0,0,0,0.6)]"
          style={{ left: `${sliderPosition}%` }}
          onMouseDown={(e) => {
            isDragging.current = true;
            handleMove(e.clientX);
          }}
          onTouchStart={(e) => {
            isDragging.current = true;
            handleMove(e.touches[0].clientX);
          }}
        >
          <div className="absolute top-1/2 -translate-y-1/2 -left-3.5 w-8 h-8 rounded-full bg-white text-slate-800 shadow-lg flex items-center justify-center border border-slate-400 hover:scale-110 transition cursor-ew-resize">
            <MoveHorizontal className="w-4 h-4 text-slate-700" />
          </div>
        </div>
      </div>
    </div>
  );
};
