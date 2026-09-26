"""
Diagnostic image generator for YOLO Building Detection & Georeferencing Pipeline.
Exports 4 distinct diagnostic visualizations:
1. Original ORI
2. ORI + YOLO Bounding Boxes
3. ORI + Segmentation Masks
4. ORI + Final Polygonized Footprints (sitting directly on top of building pixels)
"""

import os
import base64
from typing import Dict, Any, List
from pathlib import Path
import cv2
import numpy as np
import rasterio

ROOT_DIR = Path(__file__).resolve().parents[4]
DIAGNOSTIC_DIR = os.path.join(str(ROOT_DIR), "data", "demo", "diagnostics")
DEFAULT_RASTER_PATH = os.path.join(str(ROOT_DIR), "data", "uploads", "ori", "coimbatore_urban_drone_ori.tif")

class YOLODiagnosticExporter:
    def __init__(self, output_dir: str = DIAGNOSTIC_DIR):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_diagnostics(self, raster_path: str = DEFAULT_RASTER_PATH) -> Dict[str, Any]:
        from backend.app.services.ai.onnx_building_detector import onnx_detector

        if not os.path.exists(raster_path):
            raise FileNotFoundError(f"Raster file not found: {raster_path}")

        # 1. Read original GeoTIFF pixels
        with rasterio.open(raster_path) as src:
            w, h = src.width, src.height
            transform = src.transform
            crs = str(src.crs)
            bounds = list(src.bounds)
            data = src.read([1, 2, 3])
            rgb = np.transpose(data, (1, 2, 0)) # HWC

        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

        # 2. Run ONNX YOLO building detector
        buildings, meta = onnx_detector.extract_buildings_from_raster(raster_path, target_crs="EPSG:4326")

        # Image 1: Original ORI
        img1 = bgr.copy()
        img1_path = os.path.join(self.output_dir, "1_original_ori.png")
        cv2.imwrite(img1_path, img1)

        # Image 2: ORI + YOLO Bounding Boxes
        img2 = bgr.copy()
        for idx, b in enumerate(buildings):
            px_box = b.get("pixel_bbox")
            if px_box and len(px_box) == 4:
                x1, y1, x2, y2 = px_box
                conf = b.get("confidence", 0.0)
                # Draw high-contrast bounding box
                cv2.rectangle(img2, (x1, y1), (x2, y2), (0, 165, 255), 2)
                # Label
                label = f"{b['building_id']} ({conf:.1f}%)"
                cv2.putText(img2, label, (x1, max(12, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1, cv2.LINE_AA)
        img2_path = os.path.join(self.output_dir, "2_ori_yolo_bboxes.png")
        cv2.imwrite(img2_path, img2)

        # Image 3: ORI + Segmentation Masks
        img3 = bgr.copy()
        overlay3 = bgr.copy()
        inv_transform = ~transform

        for b in buildings:
            geom = b.get("geometry", {})
            coords = geom.get("coordinates", [])
            if coords and len(coords) > 0:
                exterior = coords[0]
                # Convert geographic coords back to pixel space
                px_pts = []
                for gx, gy in exterior:
                    px, py = inv_transform * (gx, gy)
                    px_pts.append([int(round(px)), int(round(py))])
                px_arr = np.array(px_pts, dtype=np.int32)
                cv2.fillPoly(overlay3, [px_arr], (0, 140, 255))
        # Blend overlay (40% mask opacity)
        cv2.addWeighted(overlay3, 0.45, img3, 0.55, 0, img3)
        img3_path = os.path.join(self.output_dir, "3_ori_segmentation_masks.png")
        cv2.imwrite(img3_path, img3)

        # Image 4: ORI + Final Polygonized Footprints (Crisp architectural contours with vertex points)
        img4 = bgr.copy()
        for b in buildings:
            geom = b.get("geometry", {})
            coords = geom.get("coordinates", [])
            if coords and len(coords) > 0:
                exterior = coords[0]
                px_pts = []
                for gx, gy in exterior:
                    px, py = inv_transform * (gx, gy)
                    px_pts.append([int(round(px)), int(round(py))])
                px_arr = np.array(px_pts, dtype=np.int32)

                # Translucent fill
                fill_layer = img4.copy()
                cv2.fillPoly(fill_layer, [px_arr], (180, 105, 255)) # Lilac fill
                cv2.addWeighted(fill_layer, 0.35, img4, 0.65, 0, img4)

                # Crisp boundary stroke
                cv2.polylines(img4, [px_arr], True, (0, 0, 230), 2, cv2.LINE_AA) # Vivid Red outline

                # Draw vertices
                for pt in px_pts[:-1]:
                    cv2.circle(img4, (pt[0], pt[1]), 3, (255, 255, 0), -1, cv2.LINE_AA)

                # Footprint label with area
                area_m2 = b.get("area_m2", 0.0)
                cx = int(np.mean([p[0] for p in px_pts]))
                cy = int(np.mean([p[1] for p in px_pts]))
                cv2.putText(img4, f"{area_m2:.0f}m2", (cx - 15, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (255, 255, 255), 1, cv2.LINE_AA)

        img4_path = os.path.join(self.output_dir, "4_ori_final_footprints.png")
        cv2.imwrite(img4_path, img4)

        def _to_base64(path):
            with open(path, "rb") as f:
                return f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"

        return {
            "status": "success",
            "raster_info": {
                "raster_path": raster_path,
                "width": w,
                "height": h,
                "crs": crs,
                "bounds": bounds,
                "buildings_detected": len(buildings)
            },
            "saved_files": {
                "original_ori": img1_path,
                "yolo_bboxes": img2_path,
                "segmentation_masks": img3_path,
                "final_footprints": img4_path
            },
            "images_base64": {
                "original_ori": _to_base64(img1_path),
                "yolo_bboxes": _to_base64(img2_path),
                "segmentation_masks": _to_base64(img3_path),
                "final_footprints": _to_base64(img4_path)
            },
            "buildings": buildings
        }

diagnostic_exporter = YOLODiagnosticExporter()
