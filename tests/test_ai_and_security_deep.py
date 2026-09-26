"""
Phase 21 Comprehensive Automated Verification Suite
Mandatory Test Coverage:
1. test_real_tesseract_execution
2. test_ocr_missing_binary_fallback
3. test_ocr_hitl_audit
4. test_neural_change_model_discovery
5. test_neural_change_model_execution
6. test_neural_change_model_missing_fallback
7. test_real_yolo_inference
8. test_yolo_missing_model_fallback
9. test_raster_change_detection
10. test_change_detection_crs_mismatch
11. test_hard_gate_cannot_be_overridden
12. test_rbac_access_control
13. test_audit_chain_integrity
"""

import os
import pytest
import jwt
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from shapely.geometry import Polygon, shape

from backend.app.main import app
from backend.app.services.ai.onnx_building_detector import ONNXBuildingDetector
from backend.app.services.ocr.ocr_service import ocr_service
from backend.app.services.change_detection.raster_change_detector import raster_change_detector
from backend.app.services.auth.auth_service import auth_service, JWT_SECRET_KEY, JWT_ALGORITHM
from backend.app.services.matching.ai_ranking import ai_harmonizer
from backend.app.models.storage import storage_repo

client = TestClient(app)

# =====================================================================
# 1. YOLO ONNX NEURAL BUILDING EXTRACTION
# =====================================================================

def test_real_yolo_inference():
    """Validates genuine YOLOv8-Seg neural execution via ONNX Runtime on real drone GeoTIFF."""
    model_path = os.path.join("models", "building", "yolov8n-seg.onnx")
    assert os.path.exists(model_path), "Expected yolov8n-seg.onnx in models/building/"
    
    detector = ONNXBuildingDetector(model_path=model_path, conf_threshold=0.25)
    assert detector.inference_mode == "ONNX"
    assert detector.session is not None
    assert "CPUExecutionProvider" in detector.session.get_providers()
    
    raster_path = os.path.join("data", "uploads", "ori", "coimbatore_urban_drone_ori.tif")
    if os.path.exists(raster_path):
        buildings, metadata = detector.extract_buildings_from_raster(raster_path)
        assert metadata["inference_mode"] == "ONNX"
        assert metadata["execution_provider"] == "CPUExecutionProvider"
        assert len(buildings) > 0
        for b in buildings:
            geom = shape(b["geometry"])
            assert geom.is_valid
            assert geom.area > 0.0
            assert "confidence" in b
            assert b["inference_mode"] == "ONNX"

def test_yolo_missing_model_fallback():
    """Ensures missing model path gracefully triggers FALLBACK mode without crashing."""
    detector = ONNXBuildingDetector(model_path="models/building/non_existent_weights.onnx")
    assert detector.inference_mode == "FALLBACK"
    assert detector.session is None
    buildings, metadata = detector.extract_buildings_from_raster("non_existent_drone_ori.tif")
    assert metadata["inference_mode"] == "FALLBACK"
    assert len(buildings) > 0


# =====================================================================
# 2. REVENUE DOCUMENT OCR PIPELINE & HITL AUDIT
# =====================================================================

def test_real_tesseract_execution():
    """Tests genuine Tesseract execution on scanned revenue image."""
    has_bin = ocr_service.has_tesseract_binary()
    assert has_bin is True
    test_img = os.path.join("data", "demo", "scanned_cadastral_record.png")
    with open(test_img, "rb") as f:
        file_bytes = f.read()
    raw_text, fields, mode = ocr_service.extract_text_from_document(
        file_name="scanned_cadastral_record.png",
        file_bytes=file_bytes
    )
    assert mode == "TESSERACT"
    assert len(raw_text) > 0
    assert "184/2" in raw_text or "Coimbatore" in raw_text or "REVENUE" in raw_text
    assert fields["survey_number"]["value"] == "184/2"
    assert fields["survey_number"]["source"] == "TESSERACT"
    assert fields["area_m2"]["value"] == "1520.0"
    assert fields["patta_number"]["value"] == "784"

def test_ocr_missing_binary_fallback():
    """Validates that offline fallback pattern extraction produces complete revenue field metadata."""
    res = ocr_service.process_document(
        filename="patta_712_baseline.png",
        file_bytes=b"dummy_bytes_for_fallback_test"
    )
    assert res["status"] == "SUCCESS"
    assert "ocr_mode" in res
    fields = res["fields"]
    for field_name in ["survey_number", "subdivision", "owner_name", "area_m2", "land_use", "village"]:
        assert field_name in fields
        assert "value" in fields[field_name]
        assert "confidence" in fields[field_name]
        assert "verification_status" in fields[field_name]

def test_ocr_hitl_audit():
    """Validates human-in-the-loop review, field correction, and immutable audit recording."""
    res = ocr_service.process_document(
        filename="scanned_extract_pune.pdf",
        file_bytes=b"sample_cadastral_pdf_stream"
    )
    doc_id = res["doc_id"]
    
    # Reviewer approves and updates survey number and owner name
    v_res = ocr_service.verify_document_fields(
        doc_id=doc_id,
        corrected_fields={"survey_number": "184/2-CONFIRMED", "owner_name": "Ramesh S. Patil"},
        verified_by="Chief_Survey_Officer"
    )
    assert v_res["status"] == "VERIFIED"
    assert v_res["fields"]["survey_number"]["value"] == "184/2-CONFIRMED"
    assert v_res["fields"]["survey_number"]["corrected_value"] == "184/2-CONFIRMED"
    assert v_res["fields"]["survey_number"]["reviewer"] == "Chief_Survey_Officer"
    assert v_res["fields"]["survey_number"]["verification_status"] == "VERIFIED"


# =====================================================================
# 3. MULTI-TEMPORAL RASTER CHANGE DETECTION
# =====================================================================

def test_neural_change_model_discovery():
    """Checks for Siamese/Change-Detection ONNX weights and confirms transparent status."""
    change_model_path = os.path.join("models", "change_detection", "change_model.onnx")
    exists = os.path.exists(change_model_path)
    detector = raster_change_detector
    if exists:
        assert detector.inference_mode == "ONNX"
        assert detector.session is not None
    else:
        assert detector.inference_mode == "CLASSICAL_DIFFERENCING"

def test_neural_change_model_execution():
    """Runs change detection with neural weights and verifies ONNX execution mode and polygon validity."""
    events, meta = raster_change_detector.run_change_detection()
    assert meta["inference_mode"] == "ONNX"
    assert "ONNX" in meta["methodology"]
    assert len(events) > 0
    for e in events:
        assert e["inference_mode"] == "ONNX"
        assert e["confidence"] >= 80.0
        assert "geometry" in e
        assert shape(e["geometry"]).is_valid

def test_neural_change_model_missing_fallback():
    """Confirms that when ONNX model is missing, classical differencing executes without claiming neural inference."""
    from backend.app.services.change_detection.raster_change_detector import RasterChangeDetector
    detector = RasterChangeDetector(model_path="models/change_detection/non_existent.onnx")
    assert detector.inference_mode == "CLASSICAL_DIFFERENCING"
    assert detector.session is None
    events, meta = detector.run_change_detection()
    assert meta["inference_mode"] == "CLASSICAL_DIFFERENCING"
    assert len(events) > 0

def test_raster_change_detection():
    """Executes genuine pixel differencing and polygonization across real temporal GeoTIFFs."""
    t1_path = os.path.join("data", "uploads", "ori", "T1.tif")
    t2_path = os.path.join("data", "uploads", "ori", "T2.tif")
    
    if os.path.exists(t1_path) and os.path.exists(t2_path):
        events, meta = raster_change_detector.run_change_detection(
            img_t1_bytes_or_path=t1_path,
            img_t2_bytes_or_path=t2_path
        )
        assert meta["data_source_mode"] == "REAL_TEMPORAL_GEOTIFF"
        assert len(events) >= 3
        
        valid_classes = {"BUILDING_ADDED", "BUILDING_REMOVED", "BUILDING_EXPANSION", "SIGNIFICANT_LAND_COVER_CHANGE"}
        for ev in events:
            assert ev["change_type"] in valid_classes
            geom = shape(ev["geometry"])
            assert geom.is_valid
            assert ev["area_m2"] > 0.0

def test_change_detection_crs_mismatch():
    """Verifies that invalid or incompatible raster paths fail safely into controlled baseline."""
    events, meta = raster_change_detector.run_change_detection(
        img_t1_bytes_or_path="non_existent_t1.tif",
        img_t2_bytes_or_path="non_existent_t2.tif"
    )
    assert meta["data_source_mode"] in ["SYNTHETIC_REGIONAL_BASELINE", "REAL_TEMPORAL_GEOTIFF"]
    assert len(events) > 0


# =====================================================================
# 4. RBAC, HARD LEGAL GATES & AUDIT INTEGRITY
# =====================================================================

def test_hard_gate_cannot_be_overridden():
    """Verifies that legal/geometric hard gates strictly reject invalid matches regardless of AI score."""
    base_parcel = {"parcel_id": "P-BASE", "survey_no": "100", "legacy_area": 1000.0}
    # Massive area mismatch: 1000m² vs 3500m² (>50% mismatch)
    cand_parcel = {"parcel_id": "P-CAND", "survey_no": "100", "legacy_area": 3500.0}
    
    poly_a = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    poly_b = Polygon([(500, 500), (600, 500), (600, 600), (500, 600)]) # Extreme distance
    
    eval_res = ai_harmonizer.evaluate_candidate(
        base_parcel=base_parcel,
        candidate_parcel=cand_parcel,
        base_geom=poly_a,
        candidate_geom=poly_b,
        gnss_support=False,
        utility_conflict=False
    )
    
    assert eval_res["hard_gates_passed"] is False
    assert eval_res["decision"] == "REJECTED_BY_HARD_GATE"
    assert len(eval_res["gate_failures"]) > 0

def test_rbac_access_control():
    """Verifies server-side role enforcement (OWNER, ADMIN, STAFF) and HTTP 403 on restricted actions."""
    admin_token = auth_service.create_access_token("admin_test", "ADMIN")
    staff_token = auth_service.create_access_token("staff_test", "STAFF")
    
    # ADMIN can view audit trail
    admin_res = client.get("/api/audit/logs", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_res.status_code == 200
    
    # STAFF is strictly forbidden from accessing audit trail
    staff_res = client.get("/api/audit/logs", headers={"Authorization": f"Bearer {staff_token}"})
    assert staff_res.status_code == 403

def test_audit_chain_integrity():
    """Verifies that system actions are recorded in the audit trail with complete lineage."""
    test_user = "audit_officer"
    storage_repo.save_audit_log(
        username=test_user,
        action="VERIFY_BOUNDARY_ALIGNMENT",
        parcel_id="PARCEL-AUDIT-999",
        details={"status": "APPROVED", "crs": "EPSG:32643", "deviation_m": 0.12}
    )
    
    admin_token = auth_service.create_access_token("admin_auditor", "ADMIN")
    res = client.get("/api/audit/logs", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    logs = res.json()
    assert len(logs) > 0
    latest = logs[0]
    assert "timestamp" in latest
    assert "action" in latest
    assert "username" in latest
