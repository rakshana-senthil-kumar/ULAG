import React, { useState, useRef, useEffect } from 'react';
import { MoveHorizontal } from 'lucide-react';

interface BeforeAfterSliderProps {
  beforeTitle?: string;
  afterTitle?: string;
  beforeYear?: string;
  afterYear?: string;
}

export const BeforeAfterSlider: React.FC<BeforeAfterSliderProps> = ({
  beforeTitle = 'Historical Cadastral',
  afterTitle = 'Current Drone ORI & AI Extracted',
  beforeYear = '2023',
  afterYear = '2026'
}) => {
  const [sliderPosition, setSliderPosition] = useState(50);
  const isDragging = useRef(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMove = (clientX: number) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    let percentage = (x / rect.width) * 100;
    if (percentage < 0) percentage = 0;
    if (percentage > 100) percentage = 100;
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

  return (
    <div className="relative w-full h-[400px] rounded-lg overflow-hidden border border-slate-300 select-none bg-slate-950 font-sans shadow-inner">
      <div
        ref={containerRef}
        className="relative w-full h-full cursor-ew-resize overflow-hidden"
        onMouseDown={(e) => {
          isDragging.current = true;
          handleMove(e.clientX);
        }}
        onTouchStart={(e) => {
          isDragging.current = true;
          handleMove(e.touches[0].clientX);
        }}
      >
        {/* AFTER Layer (Right / Full background) */}
        <div className="absolute inset-0 bg-[#0f172a] p-6 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-200 z-10">
            <span className="bg-emerald-900/80 text-emerald-200 px-3 py-1 rounded text-xs font-bold tracking-wide border border-emerald-700">
              {afterYear} — {afterTitle}
            </span>
            <span className="text-[11px] text-emerald-400 font-mono">EPSG:32643 • High-Res Drone Imagery</span>
          </div>

          {/* Canvas visualization of 2026 Drone & AI Buildings */}
          <div className="relative w-full h-full my-4 flex items-center justify-center">
            <svg className="w-full h-full opacity-80" viewBox="0 0 600 300">
              {/* Grid lines */}
              <defs>
                <pattern id="grid2026" width="40" height="40" patternUnits="userSpaceOnUse">
                  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth="1" />
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#grid2026)" />

              {/* Updated Drone Imagery Parcel Overlay (Amber & Green) */}
              <polygon points="50,40 280,30 290,200 40,210" fill="#f59e0b" fillOpacity="0.15" stroke="#d97706" strokeWidth="2.5" />
              <text x="140" y="120" fill="#fbbf24" fontSize="12" fontWeight="bold">Parcel 184/2 (1,541 m²)</text>

              <polygon points="310,35 550,45 540,230 300,210" fill="#10b981" fillOpacity="0.15" stroke="#059669" strokeWidth="2.5" />
              <text x="400" y="130" fill="#34d399" fontSize="12" fontWeight="bold">Parcel 185/1 (2,100 m²)</text>

              {/* AI Buildings Detected (Purple overlay) */}
              <rect x="80" y="70" width="60" height="45" fill="#a855f7" fillOpacity="0.5" stroke="#9333ea" strokeWidth="1.5" />
              <text x="85" y="97" fill="#ffffff" fontSize="9" fontWeight="bold">Bldg #1</text>

              <rect x="180" y="110" width="70" height="50" fill="#a855f7" fillOpacity="0.5" stroke="#9333ea" strokeWidth="1.5" />
              <text x="185" y="140" fill="#ffffff" fontSize="9" fontWeight="bold">Bldg #2</text>

              <rect x="350" y="80" width="80" height="60" fill="#a855f7" fillOpacity="0.5" stroke="#9333ea" strokeWidth="1.5" />
              <text x="355" y="115" fill="#ffffff" fontSize="9" fontWeight="bold">Bldg #3 (New)</text>
            </svg>
          </div>

          <div className="flex items-center gap-4 text-xs text-slate-400 z-10">
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded bg-emerald-500 inline-block"></span> Drone Bounds</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded bg-purple-500 inline-block"></span> AI Detected Buildings (+3)</span>
          </div>
        </div>

        {/* BEFORE Layer (Left / Clipped overlay) */}
        <div
          className="absolute inset-0 bg-[#091322] p-6 flex flex-col justify-between overflow-hidden border-r-2 border-white shadow-2xl"
          style={{ width: `${sliderPosition}%` }}
        >
          <div className="w-[600px] sm:w-[800px] md:w-[1000px] h-full flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-200 z-10">
              <span className="bg-blue-900/80 text-blue-200 px-3 py-1 rounded text-xs font-bold tracking-wide border border-blue-700">
                {beforeYear} — {beforeTitle}
              </span>
              <span className="text-[11px] text-blue-400 font-mono">EPSG:4326 • Revenue Survey Map</span>
            </div>

            {/* Canvas visualization of 2023 Historical Cadastral */}
            <div className="relative w-full h-full my-4 flex items-center justify-center">
              <svg className="w-full h-full opacity-80" viewBox="0 0 600 300">
                <defs>
                  <pattern id="grid2023" width="40" height="40" patternUnits="userSpaceOnUse">
                    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth="1" />
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid2023)" />

                {/* Legacy Vector Parcel (Blue dashed) */}
                <polygon points="60,50 270,40 280,190 50,195" fill="#3b82f6" fillOpacity="0.2" stroke="#2563eb" strokeWidth="2.5" strokeDasharray="6,4" />
                <text x="130" y="115" fill="#60a5fa" fontSize="12" fontWeight="bold">Parcel 184/2 (1,487 m²)</text>

                <polygon points="295,45 530,55 520,220 285,200" fill="#3b82f6" fillOpacity="0.2" stroke="#2563eb" strokeWidth="2.5" strokeDasharray="6,4" />
                <text x="380" y="130" fill="#60a5fa" fontSize="12" fontWeight="bold">Parcel 185/1 (2,050 m²)</text>
              </svg>
            </div>

            <div className="flex items-center gap-4 text-xs text-slate-400 z-10">
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded bg-blue-500 inline-block"></span> Historical Revenue Boundaries</span>
              <span className="text-slate-500 text-[11px]">No structural overlays</span>
            </div>
          </div>
        </div>

        {/* DRAGGABLE DIVIDER HANDLE */}
        <div
          className="absolute top-0 bottom-0 w-1 bg-white cursor-ew-resize z-30 shadow-[0_0_10px_rgba(0,0,0,0.5)]"
          style={{ left: `${sliderPosition}%` }}
        >
          <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-white text-slate-900 border-2 border-blue-600 flex items-center justify-center shadow-lg">
            <MoveHorizontal className="w-4 h-4" />
          </div>
        </div>
      </div>
    </div>
  );
};
