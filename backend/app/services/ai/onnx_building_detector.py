"""
Real Deep-Learning Building Extraction Pipeline for ULAG
Uses ONNX Runtime for local inference on drone photogrammetry / ORI rasters.
Supports CPU and GPU/CUDA execution providers.
Does NOT require internet during inference.

Pipeline:
Raw Drone Image / ORI -> Raster Windowing / Tiling -> Letterbox Preprocessing (640x640)
-> YOLOv8 Segmentation ONNX -> ONNX Runtime -> Output Parsing (Det + Protos)
-> NMS / Confidence Filtering -> Segmentation Mask Linear Combination & BBox Crop
-> Reverse Letterbox & Rescaling to Original Raster Pixels -> Morphological Cleanup
-> Contour Extraction -> Pixel-Space Simplification -> Affine Georeferencing
-> Spatial Sanity Filters (Area, Aspect Ratio, Compactness) -> Target CRS Reprojection
-> Canonical Building Footprints
"""

import os
import time
import math
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import numpy as np

try:
    import onnxruntime as ort
    HAS_ORT = True
except ImportError:
    HAS_ORT = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    import rasterio
    from rasterio.windows import Window
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False

from shapely.geometry import Polygon, MultiPolygon, shape, mapping, box
from shapely.validation import make_valid
import pyproj

ROOT_DIR = Path(__file__).resolve().parents[4]
DEFAULT_MODEL_DIR = os.path.join(str(ROOT_DIR), "models", "building")
DEFAULT_MODEL_PATH = os.path.join(DEFAULT_MODEL_DIR, "yolov8n-seg.onnx")

class ONNXBuildingDetector:
    def __init__(
        self,
        model_path: Optional[str] = None,
        conf_threshold: float = 0.80,
        iou_threshold: float = 0.45,
        min_area_m2: float = 15.0,
        max_area_m2: float = 1800.0,
        max_aspect_ratio: float = 4.5,
        min_compactness: float = 0.12
    ):
        self.model_path = model_path or os.environ.get("ULAG_YOLO_MODEL_PATH", DEFAULT_MODEL_PATH)
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.min_area_m2 = min_area_m2
        self.max_area_m2 = max_area_m2
        self.max_aspect_ratio = max_aspect_ratio
        self.min_compactness = min_compactness
        self.tile_size = 640
        self.tile_overlap = 64
        self.session = None
        self.input_name = None
        self.output_names = []
        self.execution_provider = "CPUExecutionProvider"
        self.inference_mode = "FALLBACK"
        
        self._initialize_session()

    def _initialize_session(self):
        """Initializes ONNX Runtime session if model file is found locally."""
        if not HAS_ORT or not os.path.exists(self.model_path):
            self.inference_mode = "FALLBACK"
            self.session = None
            return

        try:
            available_providers = ort.get_available_providers()
            if "CUDAExecutionProvider" in available_providers:
                providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
                self.execution_provider = "CUDAExecutionProvider"
            else:
                providers = ["CPUExecutionProvider"]
                self.execution_provider = "CPUExecutionProvider"

            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            sess_options.intra_op_num_threads = 4

            self.session = ort.InferenceSession(self.model_path, sess_options=sess_options, providers=providers)
            inputs = self.session.get_inputs()
            self.input_name = inputs[0].name
            self.output_names = [out.name for out in self.session.get_outputs()]
            self.inference_mode = "ONNX"
        except Exception as e:
            print(f"[ONNXBuildingDetector] Could not load ONNX session: {e}. Running in FALLBACK mode.")
            self.inference_mode = "FALLBACK"
            self.session = None

    def get_status(self) -> Dict[str, Any]:
        """Exposes the current runtime status, execution mode, and hardware provider."""
        return {
            "model_path": self.model_path,
            "model_exists": os.path.exists(self.model_path),
            "inference_mode": self.inference_mode,
            "framework": "ONNX Runtime" if self.inference_mode == "ONNX" else "Deterministic GIS Fallback",
            "execution_provider": self.execution_provider if self.inference_mode == "ONNX" else "CPU",
            "conf_threshold": self.conf_threshold,
            "min_area_m2": self.min_area_m2,
            "max_area_m2": self.max_area_m2,
            "tile_size": self.tile_size,
            "tile_overlap": self.tile_overlap
        }

    def _generate_raster_tiles(
        self,
        image_h: int,
        image_w: int,
        tile_size: int = 640,
        overlap: int = 64
    ) -> List[Tuple[int, int, int, int]]:
        """
        Generates window coordinates (col_off, row_off, width, height) with overlap
        to prevent boundary clipping of buildings.
        """
        if image_h <= tile_size and image_w <= tile_size:
            return [(0, 0, image_w, image_h)]

        step = tile_size - overlap
        tiles = []
        for y in range(0, image_h, step):
            for x in range(0, image_w, step):
                w = min(tile_size, image_w - x)
                h = min(tile_size, image_h - y)
                tiles.append((x, y, w, h))
        return tiles

    def _letterbox_tile(
        self,
        tile_img: np.ndarray,
        new_shape: Tuple[int, int] = (640, 640),
        color: Tuple[int, int, int] = (114, 114, 114)
    ) -> Tuple[np.ndarray, float, Tuple[float, float], Tuple[int, int]]:
        """
        Resizes tile preserving aspect ratio with letterbox padding meeting YOLO stride constraints.
        Returns: (blob [1, 3, 640, 640], ratio, (dw, dh), (unpad_w, unpad_h))
        """
        h, w = tile_img.shape[:2]
        r = min(new_shape[0] / float(h), new_shape[1] / float(w))
        unpad_w = int(round(w * r))
        unpad_h = int(round(h * r))
        dw = (new_shape[1] - unpad_w) / 2.0
        dh = (new_shape[0] - unpad_h) / 2.0

        if (w, h) != (unpad_w, unpad_h):
            if HAS_CV2:
                resized = cv2.resize(tile_img, (unpad_w, unpad_h), interpolation=cv2.INTER_LINEAR)
            else:
                resized = tile_img
        else:
            resized = tile_img

        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))

        if HAS_CV2:
            padded = cv2.copyMakeBorder(resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
        else:
            padded = np.full((new_shape[0], new_shape[1], 3), color[0], dtype=tile_img.dtype)
            padded[top:top+unpad_h, left:left+unpad_w] = resized

        # Normalize RGB [0, 255] -> [0.0, 1.0] float32
        blob = padded.astype(np.float32) / 255.0
        # HWC -> CHW -> NCHW
        blob = np.transpose(blob, (2, 0, 1))
        blob = np.expand_dims(blob, axis=0)

        return blob, r, (dw, dh), (unpad_w, unpad_h)

    def _decode_yolo_segmentation(
        self,
        det: np.ndarray,
        proto: np.ndarray,
        tile_w: int,
        tile_h: int,
        col_off: int,
        row_off: int,
        r: float,
        dw: float,
        dh: float,
        unpad_dims: Tuple[int, int],
        affine_transform: Any,
        target_crs: str,
        transformer: Optional[Any] = None,
        conf_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Decodes YOLOv8 segmentation outputs:
        - Det shape: (4 + num_classes + 32, 8400)
        - Proto shape: (32, 160, 160)
        - Extracts bounding boxes, applies NMS, computes prototype mask combinations,
        - Crops mask to detection bounding box, removes letterbox padding,
        - Restores mask to original raster pixel coordinates,
        - Simplifies contours in pixel space (approxPolyDP),
        - Transforms to geospatial coordinates via raster affine transform,
        - Applies spatial sanity filters (min/max area, aspect ratio, compactness).
        """
        if not HAS_CV2:
            return []

        eff_conf = conf_threshold if conf_threshold is not None else self.conf_threshold
        num_classes = det.shape[0] - 4 - 32
        boxes = det[:4, :].T
        scores = det[4:4 + num_classes, :].T
        mask_coeffs = det[4 + num_classes:, :].T

        max_scores = np.max(scores, axis=1)
        keep_idxs = np.where(max_scores >= eff_conf)[0]

        if len(keep_idxs) == 0:
            return []

        nms_boxes = []
        nms_scores = []
        for idx in keep_idxs:
            cx, cy, bw, bh = boxes[idx]
            x1 = int(cx - bw / 2.0)
            y1 = int(cy - bh / 2.0)
            nms_boxes.append([x1, y1, int(bw), int(bh)])
            nms_scores.append(float(max_scores[idx]))

        indices = cv2.dnn.NMSBoxes(nms_boxes, nms_scores, eff_conf, self.iou_threshold)
        if len(indices) == 0:
            return []

        if isinstance(indices, np.ndarray):
            indices = indices.flatten()

        proto_flat = proto.reshape(32, 160 * 160)
        unpad_w, unpad_h = unpad_dims
        valid_detections = []

        for i in indices:
            idx = keep_idxs[i]
            conf = float(max_scores[idx])
            coeff = mask_coeffs[idx]
            cx, cy, bw, bh = boxes[idx]

            # 1. Prototype linear combination & sigmoid
            mask_160 = 1.0 / (1.0 + np.exp(-np.dot(coeff, proto_flat))).reshape(160, 160)
            mask_640 = cv2.resize(mask_160, (640, 640), interpolation=cv2.INTER_LINEAR)

            # 2. Crop mask to detection bounding box in 640 space
            bx1 = max(0, int(cx - bw / 2.0))
            by1 = max(0, int(cy - bh / 2.0))
            bx2 = min(640, int(cx + bw / 2.0))
            by2 = min(640, int(cy + bh / 2.0))

            bbox_mask = np.zeros((640, 640), dtype=np.float32)
            bbox_mask[by1:by2, bx1:bx2] = 1.0
            mask_640 = mask_640 * bbox_mask

            # 3. Remove letterbox padding
            crop_y1 = int(round(dh))
            crop_y2 = int(round(dh + unpad_h))
            crop_x1 = int(round(dw))
            crop_x2 = int(round(dw + unpad_w))
            mask_cropped = mask_640[crop_y1:crop_y2, crop_x1:crop_x2]

            # 4. Reverse scale to original raster tile dimensions
            mask_tile = cv2.resize(mask_cropped, (tile_w, tile_h), interpolation=cv2.INTER_LINEAR)
            binary_mask = (mask_tile > 0.45).astype(np.uint8) * 255

            # 5. Morphological closing to remove boundary noise
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)
            mask_pixel_count = int(np.count_nonzero(binary_mask))

            # 6. Extract contours in tile pixel space
            contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                continue

            for cnt in contours:
                if cv2.contourArea(cnt) < 15:
                    continue

                # 7. Pixel-space Douglas-Peucker simplification (prevents geographic degree destruction)
                cnt_simp = cv2.approxPolyDP(cnt, epsilon=1.0, closed=True)
                if len(cnt_simp) < 3:
                    continue

                pts = cnt_simp.squeeze(axis=1).astype(np.float64)
                if len(pts.shape) != 2 or pts.shape[0] < 3:
                    continue

                # Tile pixel coordinates to full raster pixel coordinates
                pts[:, 0] += col_off
                pts[:, 1] += row_off

                # 8. Transform pixel (px, py) to raster CRS coordinates (gx, gy)
                geo_pts = [affine_transform * (px, py) for px, py in pts]
                poly = Polygon(geo_pts)
                if not poly.is_valid:
                    poly = make_valid(poly)
                if poly.is_empty or poly.area <= 0:
                    continue

                # Reproject if transformer provided
                if transformer:
                    from shapely.ops import transform as shp_transform
                    poly = shp_transform(transformer.transform, poly)

                # 9. Spatial sanity filters
                area_m2 = abs(poly.area) * (111139.0 ** 2) if "4326" in target_crs else abs(poly.area)
                b = poly.bounds
                w_m = (b[2] - b[0]) * 109093.0 if "4326" in target_crs else (b[2] - b[0])
                h_m = (b[3] - b[1]) * 111139.0 if "4326" in target_crs else (b[3] - b[1])
                aspect = max(w_m, h_m) / max(min(w_m, h_m), 1.0)
                perim_m = poly.length * 111139.0 if "4326" in target_crs else poly.length
                compactness = (4.0 * math.pi * area_m2) / (perim_m ** 2) if perim_m > 0 else 0

                # Validate against physical building thresholds
                if not (self.min_area_m2 <= area_m2 <= self.max_area_m2):
                    continue
                if w_m > 70.0 or h_m > 70.0:
                    continue
                if aspect > self.max_aspect_ratio:
                    continue
                if compactness < self.min_compactness:
                    continue

                # Pixel bbox in original raster space
                px_x1 = max(0, int((bx1 - dw) / r)) + col_off
                px_y1 = max(0, int((by1 - dh) / r)) + row_off
                px_x2 = min(tile_w, int((bx2 - dw) / r)) + col_off
                px_y2 = min(tile_h, int((by2 - dh) / r)) + row_off

                c_x, c_y = poly.centroid.x, poly.centroid.y
                v_count = len(poly.exterior.coords) - 1 if hasattr(poly, "exterior") else len(pts)

                det_record = {
                    "geometry": poly,
                    "confidence": round(conf * 100.0, 1),
                    "area_m2": round(area_m2, 1),
                    "centroid": [round(c_x, 7), round(c_y, 7)],
                    "bbox": [round(x, 7) for x in b],
                    "pixel_bbox": [px_x1, px_y1, px_x2, px_y2],
                    "mask_pixel_count": mask_pixel_count,
                    "vertex_count": v_count,
                    "crs": target_crs,
                    "source_raster_coordinates": {
                        "col_off": col_off,
                        "row_off": row_off,
                        "tile_w": tile_w,
                        "tile_h": tile_h
                    }
                }
                valid_detections.append(det_record)
                print(f"[YOLOv8-Seg] Detection: Conf={conf:.1%}, Area={area_m2:.1f} m², Vertices={v_count}, PixelBox=[{px_x1}, {px_y1}, {px_x2}, {px_y2}]")

        return valid_detections

    def _run_synthetic_demo_extraction(
        self,
        target_crs: str = "EPSG:4326"
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Fallback simulation used only when ONNX session cannot be initialized (missing weights).
        """
        demo_polygons = [
            Polygon([(76.9515, 11.0015), (76.9518, 11.0015), (76.9518, 11.0018), (76.9515, 11.0018), (76.9515, 11.0015)]),
            Polygon([(76.9525, 11.0025), (76.9529, 11.0025), (76.9529, 11.0028), (76.9525, 11.0028), (76.9525, 11.0025)]),
        ]
        buildings = []
        for i, poly in enumerate(demo_polygons):
            b_bounds = list(poly.bounds)
            buildings.append({
                "building_id": f"BLDG-FB-{i+1:04d}",
                "confidence": 82.0,
                "source": "SYNTHETIC_FALLBACK",
                "model": "YOLOv8-Seg",
                "inference_mode": "FALLBACK",
                "geometry": mapping(poly),
                "area_m2": 150.0,
                "centroid": [poly.centroid.x, poly.centroid.y],
                "bbox": b_bounds,
                "pixel_bbox": [100, 100, 200, 200],
                "mask_pixel_count": 500,
                "bbox_geometry": mapping(box(*b_bounds)),
                "segmentation_mask_geometry": mapping(poly),
                "source_raster_coordinates": [[100, 100], [200, 100], [200, 200], [100, 200]],
                "vertex_count": len(poly.exterior.coords) - 1,
                "crs": target_crs,
                "status": "FALLBACK"
            })
        metadata = {
            "model_name": "YOLOv8-Seg (Deterministic Fallback)",
            "inference_mode": "FALLBACK",
            "execution_provider": "CPU",
            "building_count": len(buildings),
            "latency_ms": 1.0,
            "message": "Fallback building extraction executed due to missing ONNX model.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return buildings, metadata

    def extract_buildings_from_raster(
        self,
        raster_path: str,
        target_crs: str = "EPSG:4326",
        conf_threshold: Optional[float] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Windowed processing on GeoTIFF orthomosaic.
        Never loads multi-hundred-MB or GB rasters entirely into RAM.
        Runs ONNX Runtime inference if session is ready.
        Does NOT inject fake demo buildings if 0 detections occur during ONNX inference.
        """
        if self.inference_mode == "FALLBACK":
            return self._run_synthetic_demo_extraction(target_crs=target_crs)

        eff_conf = conf_threshold if conf_threshold is not None else self.conf_threshold
        start_time = time.time()
        extracted_buildings = []
        tile_count = 0

        if not HAS_RASTERIO or not os.path.exists(raster_path):
            return [], {
                "model_name": "YOLOv8-Seg",
                "inference_mode": "ERROR",
                "message": f"Raster file not found: {raster_path}",
                "building_count": 0,
                "latency_ms": 0.0
            }

        try:
            with rasterio.open(raster_path) as src:
                src_crs = str(src.crs or "EPSG:4326")
                w_full, h_full = src.width, src.height
                transform = src.transform

                transformer = None
                if src_crs != target_crs:
                    transformer = pyproj.Transformer.from_crs(src_crs, target_crs, always_xy=True)

                tiles = self._generate_raster_tiles(h_full, w_full, self.tile_size, self.tile_overlap)
                tile_count = len(tiles)
                detection_idx = 1

                for (col_off, row_off, w, h) in tiles:
                    window = Window(col_off, row_off, w, h)
                    bands_to_read = min(3, src.count)
                    tile_data = src.read(list(range(1, bands_to_read + 1)), window=window)

                    if tile_data.shape[0] < 3:
                        tile_data = np.repeat(tile_data, 3, axis=0)

                    # CHW -> HWC
                    tile_img = np.transpose(tile_data, (1, 2, 0))

                    if self.session is not None and self.inference_mode == "ONNX":
                        blob, r, (dw, dh), unpad_dims = self._letterbox_tile(tile_img)
                        outputs = self.session.run(self.output_names, {self.input_name: blob})

                        det = outputs[0][0]
                        proto = outputs[1][0]

                        tile_detections = self._decode_yolo_segmentation(
                            det=det,
                            proto=proto,
                            tile_w=w,
                            tile_h=h,
                            col_off=col_off,
                            row_off=row_off,
                            r=r,
                            dw=dw,
                            dh=dh,
                            unpad_dims=unpad_dims,
                            affine_transform=transform,
                            target_crs=target_crs,
                            transformer=transformer,
                            conf_threshold=eff_conf
                        )
                    else:
                        tile_detections = []

                    for d in tile_detections:
                        b_id = f"BLD-ONNX-{detection_idx:04d}"
                        detection_idx += 1
                        poly = d["geometry"]
                        b_bounds = d["bbox"]

                        extracted_buildings.append({
                            "building_id": b_id,
                            "geometry": mapping(poly),
                            "confidence": d["confidence"],
                            "source": "DRONE_ORI",
                            "model": "YOLOv8-Seg",
                            "inference_mode": self.inference_mode,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "area_m2": d["area_m2"],
                            "centroid": d["centroid"],
                            "bbox": b_bounds,
                            "pixel_bbox": d["pixel_bbox"],
                            "mask_pixel_count": d["mask_pixel_count"],
                            "bbox_geometry": mapping(box(*b_bounds)),
                            "segmentation_mask_geometry": mapping(poly),
                            "source_raster_coordinates": d["source_raster_coordinates"],
                            "vertex_count": d["vertex_count"],
                            "crs": target_crs,
                            "status": "CONFIRMED"
                        })

        except Exception as e:
            print(f"[ONNXBuildingDetector] Error reading raster: {e}")
            return [], {
                "model_name": "YOLOv8-Seg",
                "inference_mode": "ERROR",
                "error": str(e),
                "building_count": 0,
                "latency_ms": round((time.time() - start_time) * 1000.0, 2)
            }

        latency_ms = round((time.time() - start_time) * 1000.0, 2)
        metadata = {
            "model_name": "YOLOv8-Seg",
            "inference_mode": self.inference_mode,
            "execution_provider": self.execution_provider,
            "tiles_processed": tile_count,
            "building_count": len(extracted_buildings),
            "latency_ms": latency_ms,
            "message": "Detection completed" if len(extracted_buildings) > 0 else "No valid YOLO building detections.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        return extracted_buildings, metadata

    def extract_building_footprints(
        self,
        raster_path: Optional[str] = None,
        confidence_threshold: float = 0.35,
        simplify_tolerance: float = 0.30,
        target_crs: str = "EPSG:4326"
    ) -> List[Dict[str, Any]]:
        if not raster_path or not os.path.exists(raster_path):
            buildings, _ = self._run_synthetic_demo_extraction(target_crs=target_crs)
            return buildings
        buildings, _ = self.extract_buildings_from_raster(
            raster_path, target_crs=target_crs, conf_threshold=confidence_threshold
        )
        return buildings

onnx_detector = ONNXBuildingDetector()
