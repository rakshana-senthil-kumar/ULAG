"""
Raw Drone ORI / Orthomosaic Ingestion & Chunked Raster Processing Service
Supports GeoTIFF, Cloud-Optimized GeoTIFF (COG), RGB and RGB+NIR imagery.
Uses windowed/chunked processing so multi-hundred-MB or multi-GB rasters
are NEVER loaded entirely into RAM.
Extracts GSD, CRS, bounds, resolution, and generates preview tiles.
"""

import os
import io
import time
import math
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import numpy as np

try:
    import rasterio
    from rasterio.windows import Window
    from rasterio.transform import from_bounds
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

from PIL import Image
from backend.app.models.storage import storage_repo

ROOT_DIR = Path(__file__).resolve().parents[4]
UPLOAD_DIR = os.path.join(str(ROOT_DIR), "data", "uploads", "ori")
DEMO_DIR = os.path.join(str(ROOT_DIR), "data", "demo")

class ORIRasterService:
    def __init__(self, upload_dir: str = UPLOAD_DIR):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)
        self.active_rasters: Dict[str, Dict[str, Any]] = {}
        self._ensure_demo_ori()

    def _ensure_demo_ori(self):
        """Ensures a demo orthomosaic GeoTIFF exists with valid metadata."""
        demo_path = os.path.join(self.upload_dir, "coimbatore_urban_drone_ori.tif")
        if os.path.exists(demo_path):
            self._register_raster_metadata("ORI-COIMBATORE-01", demo_path)
            return

        if not HAS_RASTERIO:
            return

        try:
            # Generate a lightweight demo orthomosaic GeoTIFF (3-band RGB)
            west, south, east, north = 76.9500, 11.0000, 76.9600, 11.0100
            width, height = 400, 400
            transform = from_bounds(west, south, east, north, width, height)

            # Synthetic drone RGB imagery pattern
            img_r = np.random.randint(90, 160, (height, width), dtype=np.uint8)
            img_g = np.random.randint(110, 190, (height, width), dtype=np.uint8)
            img_b = np.random.randint(80, 140, (height, width), dtype=np.uint8)

            # Add geometric building shapes in raster
            for i in range(5):
                bx, by = 60 + i * 60, 80 + i * 50
                img_r[by:by+35, bx:bx+45] = 210
                img_g[by:by+35, bx:bx+45] = 180
                img_b[by:by+35, bx:bx+45] = 150

            with rasterio.open(
                demo_path,
                "w",
                driver="GTiff",
                height=height,
                width=width,
                count=3,
                dtype=np.uint8,
                crs="EPSG:4326",
                transform=transform
            ) as dst:
                dst.write(img_r, 1)
                dst.write(img_g, 2)
                dst.write(img_b, 3)

            self._register_raster_metadata("ORI-COIMBATORE-01", demo_path)
        except Exception as e:
            print(f"[ORIRasterService] Warning creating demo ORI: {e}")

    def ingest_ori_file(
        self,
        file_name: str,
        file_bytes: bytes,
        source_name: str = "High-Resolution Drone Photogrammetry"
    ) -> Dict[str, Any]:
        """
        Saves uploaded GeoTIFF/COG and extracts rich geospatial metadata
        without reading the full image into memory at once.
        """
        # Secure filename & save to isolated upload path
        safe_name = os.path.basename(file_name).replace(" ", "_")
        target_path = os.path.join(self.upload_dir, f"{int(time.time())}_{safe_name}")

        with open(target_path, "wb") as f:
            f.write(file_bytes)

        raster_id = f"ORI-{int(time.time())}"
        return self._register_raster_metadata(raster_id, target_path, source_name)

    def _register_raster_metadata(
        self,
        raster_id: str,
        file_path: str,
        source_name: str = "Drone Orthomosaic (ORI)"
    ) -> Dict[str, Any]:
        """Extracts metadata via rasterio headers without loading raster array."""
        meta = {
            "raster_id": raster_id,
            "file_name": os.path.basename(file_path),
            "file_path": file_path,
            "file_size_mb": round(os.path.getsize(file_path) / (1024 * 1024), 2),
            "source_name": source_name,
            "crs": "EPSG:4326",
            "width": 1000,
            "height": 1000,
            "band_count": 3,
            "bands_description": ["Red", "Green", "Blue"],
            "resolution": 0.05,
            "gsd_cm_per_pixel": 5.0,
            "bounds": [76.9500, 11.0000, 76.9600, 11.0100],
            "is_cog": False,
            "format": "GeoTIFF",
            "ingested_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        if HAS_RASTERIO:
            try:
                with rasterio.open(file_path) as src:
                    b = src.bounds
                    crs_str = str(src.crs or "EPSG:4326")
                    res_x, res_y = src.res

                    # GSD estimation in cm: if degrees, multiply by 11113900 cm/deg
                    if "4326" in crs_str:
                        gsd_cm = round(res_x * 11113900.0, 1)
                    else:
                        gsd_cm = round(res_x * 100.0, 1)

                    band_names = ["Red", "Green", "Blue"]
                    if src.count == 4:
                        band_names.append("Near-Infrared (NIR)")
                    elif src.count == 1:
                        band_names = ["Panchromatic/Grayscale"]

                    meta.update({
                        "crs": crs_str,
                        "width": src.width,
                        "height": src.height,
                        "band_count": src.count,
                        "bands_description": band_names,
                        "resolution": round(res_x, 6),
                        "gsd_cm_per_pixel": gsd_cm,
                        "bounds": [round(b.left, 6), round(b.bottom, 6), round(b.right, 6), round(b.top, 6)],
                        "is_cog": bool(src.is_tiled and src.overviews(1)),
                        "format": "Cloud-Optimized GeoTIFF" if (src.is_tiled and src.overviews(1)) else "GeoTIFF"
                    })
            except Exception as e:
                print(f"[ORIRasterService] Error parsing headers: {e}")

        self.active_rasters[raster_id] = meta
        return meta

    def inspect_ori_raster(self, file_path: str, source_name: str = "Uploaded Drone ORI") -> Dict[str, Any]:
        """Inspects and registers a raw GeoTIFF/COG raster extracting GSD, CRS, bounds without full RAM load."""
        raster_id = f"ORI-{os.urandom(4).hex().upper()}"
        return self._register_raster_metadata(raster_id, file_path, source_name)

    def get_raster_metadata(self, raster_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns metadata for all ingested orthomosaic rasters."""
        if raster_id and raster_id in self.active_rasters:
            return [self.active_rasters[raster_id]]
        return list(self.active_rasters.values())

    def read_window_preview(
        self,
        raster_id: str,
        bbox: Optional[List[float]] = None,
        max_size: int = 512
    ) -> Optional[bytes]:
        """
        Reads a windowed preview of the raster without reading the full file into memory.
        Returns JPEG bytes for fast WebGIS raster tile rendering.
        """
        meta = self.active_rasters.get(raster_id)
        if not meta or not os.path.exists(meta["file_path"]):
            return None

        if not HAS_RASTERIO:
            return None

        try:
            with rasterio.open(meta["file_path"]) as src:
                if bbox:
                    from rasterio.windows import from_bounds
                    win = from_bounds(bbox[0], bbox[1], bbox[2], bbox[3], src.transform)
                else:
                    win = Window(0, 0, min(src.width, 1024), min(src.height, 1024))

                data = src.read(list(range(1, min(4, src.count + 1))), window=win)
                if data.shape[0] == 1:
                    data = np.repeat(data, 3, axis=0)

                img_np = np.transpose(data, (1, 2, 0))
                # Resize to max_size for fast transmission
                pil_img = Image.fromarray(img_np.astype(np.uint8))
                pil_img.thumbnail((max_size, max_size))

                buf = io.BytesIO()
                pil_img.save(buf, format="JPEG", quality=85)
                return buf.getvalue()
        except Exception as e:
            print(f"[ORIRasterService] Error reading window preview: {e}")
            return None

ori_service = ORIRasterService()
