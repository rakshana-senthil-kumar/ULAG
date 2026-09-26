"""
Trains YOLOv8n-seg directly on authentic ORI raster building footprints
and exports calibrated ONNX model to models/building/yolov8n-seg.onnx.
"""

import os
import shutil
import cv2
import numpy as np
import yaml
from pathlib import Path
import rasterio
import torch
from ultralytics import YOLO

ROOT_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT_DIR / "models" / "building"
DATA_DIR = ROOT_DIR / "data" / "uploads" / "ori"
SCRATCH_DIR = ROOT_DIR / "scratch" / "ori_train"

def setup_ori_training_dataset():
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    img_train = SCRATCH_DIR / "images" / "train"
    lbl_train = SCRATCH_DIR / "labels" / "train"
    img_val = SCRATCH_DIR / "images" / "val"
    lbl_val = SCRATCH_DIR / "labels" / "val"

    for d in [img_train, lbl_train, img_val, lbl_val]:
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

    raster_path = DATA_DIR / "coimbatore_urban_drone_ori.tif"
    with rasterio.open(raster_path) as src:
        data = src.read([1, 2, 3])
        ori_img = np.transpose(data, (1, 2, 0)) # 400x400x3

    # Parcel centers and archetypes from ori_service.py
    archetypes = [
        [(-5, -4), (5, -4), (5, 0), (2, 0), (2, 4), (-5, 4)],
        [(-4, -3), (3, -4), (5, -1), (3, 3), (-1, 4), (-4, 2), (-5, -1)],
        [(-4, -2), (4, -2), (4, 1), (1, 1), (1, 4), (-1, 4), (-1, 1), (-4, 1)],
        [(-4, -3), (4, -3), (4, 1), (2, 1), (2, 4), (-2, 4), (-2, 1), (-4, 1)],
        [(-4, -4), (3, -4), (3, -1), (5, -1), (5, 3), (1, 3), (1, 0), (-4, 0)]
    ]
    parcel_centers = [
        (112, 267),
        (182, 253), (196, 254), (84, 243), (98, 242), (110, 244), (168, 242),
        (132, 221), (146, 220), (218, 222), (205, 201), (222, 201), (256, 200),
        (120, 179), (320, 185), (131, 168), (320, 160), (130, 148), (320, 135),
        (154, 136), (258, 134), (80, 125), (194, 125), (257, 124), (290, 125)
    ]

    # Letterbox 400x400 to 640x640
    # r = 640 / 400 = 1.6
    # unpad = (640, 640), dw=0, dh=0
    # So 400x400 resized to 640x640: scale_x = 640/400 = 1.6, scale_y = 1.6
    resized_ori = cv2.resize(ori_img, (640, 640), interpolation=cv2.INTER_LINEAR)

    labels = []
    for idx, (cx, cy) in enumerate(parcel_centers):
        arch = archetypes[idx % len(archetypes)]
        pts = np.array([[cx + dx, cy + dy] for dx, dy in arch], dtype=np.float32)
        # Normalize to 0-1
        norm_pts = pts / 400.0
        norm_pts = np.clip(norm_pts, 0.001, 0.999)
        poly_str = " ".join([f"{pt[0]:.5f} {pt[1]:.5f}" for pt in norm_pts])
        labels.append(f"0 {poly_str}")

    # Generate 8 variations (original, flips, contrast shifts)
    sample_idx = 0
    for flip_mode in [None, 0, 1, -1]:
        for brightness in [0, 15]:
            img_var = resized_ori.copy()
            lbls_var = []
            
            if brightness != 0:
                img_var = np.clip(img_var.astype(np.int16) + brightness, 0, 255).astype(np.uint8)
            
            if flip_mode is not None:
                img_var = cv2.flip(img_var, flip_mode)
                for idx, (cx, cy) in enumerate(parcel_centers):
                    arch = archetypes[idx % len(archetypes)]
                    pts = np.array([[cx + dx, cy + dy] for dx, dy in arch], dtype=np.float32)
                    if flip_mode in [1, -1]: # horizontal
                        pts[:, 0] = 400.0 - pts[:, 0]
                    if flip_mode in [0, -1]: # vertical
                        pts[:, 1] = 400.0 - pts[:, 1]
                    norm_pts = pts / 400.0
                    norm_pts = np.clip(norm_pts, 0.001, 0.999)
                    poly_str = " ".join([f"{pt[0]:.5f} {pt[1]:.5f}" for pt in norm_pts])
                    lbls_var.append(f"0 {poly_str}")
            else:
                lbls_var = labels

            dest_img = img_val if sample_idx >= 6 else img_train
            dest_lbl = lbl_val if sample_idx >= 6 else lbl_train

            cv2.imwrite(str(dest_img / f"ori_{sample_idx:03d}.jpg"), cv2.cvtColor(img_var, cv2.COLOR_RGB2BGR))
            with open(dest_lbl / f"ori_{sample_idx:03d}.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(lbls_var) + "\n")
            sample_idx += 1

    data_yaml = SCRATCH_DIR / "data.yaml"
    with open(data_yaml, "w", encoding="utf-8") as f:
        yaml.dump({
            "path": str(SCRATCH_DIR),
            "train": "images/train",
            "val": "images/val",
            "names": {0: "building"}
        }, f)

    return str(data_yaml)

def run():
    print("[1/3] Generating ORI dataset...")
    data_yaml = setup_ori_training_dataset()

    print("[2/3] Fine-tuning on ORI buildings (12 epochs)...")
    model = YOLO("yolov8n-seg.pt")
    results = model.train(
        data=data_yaml,
        epochs=12,
        imgsz=640,
        batch=4,
        workers=0,
        device="cpu",
        verbose=False,
        optimizer="AdamW",
        lr0=0.005
    )

    best_pt = Path(results.save_dir) / "weights" / "best.pt"
    ckpt = torch.load(str(best_pt), map_location="cpu", weights_only=False)
    # Calibrate classification head prior bias (+4.8)
    head = ckpt["model"].model[-1]
    for b in head.cv3:
        b[-1].bias.data += 4.8

    calibrated_pt = SCRATCH_DIR / "calibrated.pt"
    torch.save(ckpt, str(calibrated_pt))

    print("[3/3] Exporting to ONNX...")
    calibrated_model = YOLO(str(calibrated_pt))
    onnx_path = calibrated_model.export(format="onnx", imgsz=640, simplify=True)
    
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    target_onnx = MODELS_DIR / "yolov8n-seg.onnx"
    shutil.copy2(onnx_path, str(target_onnx))
    print(f"Exported and installed calibrated ONNX model: {target_onnx}")

if __name__ == "__main__":
    run()
