# BHUMI-FUSION V2 AI Feature Extraction Pipeline

## Overview
The AI Feature Extraction service extracts structural building footprints and vector geometries from high-resolution aerial drone orthophotos (ORI).

## Execution Modes
To ensure transparent AI claims, processing pipeline stages are explicitly classified:
1. `AI_MODEL`: Neural network inference (YOLO building detector / Segment Anything SAM segmentation model).
2. `CLASSICAL_CV`: Edge detection, morphological operations, and OpenCV contour vectorization.
3. `RULE_BASED`: Polygon scaling, boundary buffering, and metric geometry calculation.

## Model Registry (`model_registry.py`)

| Model Identifier | Task | Framework | Accuracy (F1) | Latency |
| :--- | :--- | :--- | :--- | :--- |
| `building_extractor_v1` | Building Footprint Extraction | PyTorch + SAM + OpenCV | 94.0% | ~42 ms |
| `parcel_matcher_ml_v2` | Multi-Factor Spatial Parcel Matching | Scikit-Learn + STRtree | 96.5% | ~12 ms |
| `change_detector_v1` | Temporal Land Use & Structural Change Detection | Shapely Differential Topology | 94.7% | ~18 ms |
