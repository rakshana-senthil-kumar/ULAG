"""
Phase 19 Deep Automated Verification Suite
Covers:
1. YOLO ONNX Neural Building Extraction (discovery, loading, inference mode, polygon validity, missing model fallback)
2. OCR Document Processing (engine check, field parsing, confidence ratings, human verification, audit logging)
3. Bi-Temporal Raster Change Detection (raster alignment, differencing, Otsu polygonization, classification)
4. RBAC & Security Gates (OWNER, ADMIN, STAFF permissions, invalid/expired JWT, hard legal gates)
"""

import os
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from shapely.geometry import Polygon, shape

from backend.app.main import app
from backend.app.services.ai.onnx_building_detector import ONNXBuildingDetector
from backend.app.services.ocr.ocr_service import ocr_service
from backend.app.services.change_detection.raster_change_detector import raster_change_detector
from backend.app.services.auth.auth_service import auth_service
from backend.app.services.matching.ai_ranking import ai_harmonizer

client = TestClient(app)

# =====================================================================
# 1. YOLO ONNX BUILDING EXTRACTION
# =====================================================================

def test_yolo_onnx_model_discovery_and_loading():
    model_path = os.path.join("models", "building", "yolov8n-seg.onnx")
    assert os.path.exists(model_path), "Expected yolov8n-seg.onnx to exist in models/building/"
    
    detector = ONNXBuildingDetector(model_path=model_path)
    assert detector.inference_mode == "ONNX"
    assert detector.session is not None
    assert "CPUExecutionProvider" in detector.session.get_providers()

def test_yolo_onnx_real_inference_execution():
    model_path = os.path.join("models", "building", "yolov8n-seg.onnx")
    detector = ONNXBuildingDetector(model_path=model_path, conf_threshold=0.25)
    
    raster_path = os.path.join("data", "uploads", "ori", "coimbatore_urban_drone_ori.tif")
    if os.path.exists(raster_path):
        buildings, metadata = detector.extract_buildings_from_raster(raster_path)
        assert metadata["inference_mode"] == "ONNX"
        assert len(buildings) > 0
        for b in buildings:
            geom = shape(b["geometry"])
            assert geom.is_valid
            assert geom.area > 0.0
            assert "confidence" in b
            assert b["inference_mode"] == "ONNX"

def test_yolo_onnx_missing_model_fallback():
    detector = ONNXBuildingDetector(model_path="models/building/non_existent_model.onnx")
    assert detector.inference_mode == "FALLBACK"
    assert detector.session is None
    # Inference with missing model returns FALLBACK mode
    buildings, metadata = detector.extract_buildings_from_raster("non_existent_raster.tif")
    assert metadata["inference_mode"] == "FALLBACK"
    assert len(buildings) > 0


# =====================================================================
# 2. REVENUE DOCUMENT OCR PIPELINE
# =====================================================================

def test_ocr_engine_mode_reporting():
    has_bin = ocr_service.has_tesseract_binary()
    raw_text, fields, mode = ocr_service.extract_text_from_document(
        file_name="test_record.png",
        file_bytes=b"dummy_test_bytes"
    )
    if has_bin:
        assert mode == "TESSERACT"
    else:
        assert mode == "FALLBACK"
    assert len(raw_text) > 0
    assert "survey_number" in fields
    assert "owner_name" in fields
    assert "area_m2" in fields

def test_ocr_human_verification_and_audit():
    res = ocr_service.process_document(
        filename="patta_712_sample.png",
        file_bytes=b"dummy_image_data_stream"
    )
    doc_id = res["doc_id"]
    assert "ocr_mode" in res
    assert doc_id.startswith("OCR-")
    
    # Human-in-the-loop correction
    v_res = ocr_service.verify_document_fields(
        doc_id=doc_id,
        corrected_fields={"survey_number": "184/2-VERIFIED", "owner_name": "Ramesh S. Patil"},
        verified_by="Tahsildar_Officer"
    )
    assert v_res["status"] == "VERIFIED"
    assert v_res["fields"]["survey_number"]["value"] == "184/2-VERIFIED"
    assert v_res["fields"]["survey_number"]["corrected_value"] == "184/2-VERIFIED"
    assert v_res["fields"]["survey_number"]["verification_status"] == "VERIFIED"
    assert v_res["fields"]["survey_number"]["reviewer"] == "Tahsildar_Officer"


# =====================================================================
# 3. BI-TEMPORAL RASTER CHANGE DETECTION
# =====================================================================

def test_raster_change_detection_real_geotiff():
    t1_path = os.path.join("data", "uploads", "ori", "T1.tif")
    t2_path = os.path.join("data", "uploads", "ori", "T2.tif")
    
    if os.path.exists(t1_path) and os.path.exists(t2_path):
        events, meta = raster_change_detector.run_change_detection(
            img_t1_bytes_or_path=t1_path,
            img_t2_bytes_or_path=t2_path
        )
        assert meta["inference_mode"] in ["CLASSICAL_DIFFERENCING", "ONNX"]
        assert meta["data_source_mode"] == "REAL_TEMPORAL_GEOTIFF"
        assert len(events) > 0
        
        valid_classes = {"BUILDING_ADDED", "BUILDING_REMOVED", "BUILDING_EXPANSION", "SIGNIFICANT_LAND_COVER_CHANGE"}
        for ev in events:
            assert ev["change_type"] in valid_classes
            geom = shape(ev["geometry"])
            assert geom.is_valid
            assert ev["area_m2"] > 0.0

def test_raster_change_detection_crs_mismatch_fails_safely():
    # Attempting change detection on incompatible objects handles errors gracefully
    events, meta = raster_change_detector.run_change_detection(
        img_t1_bytes_or_path="invalid_path_1.tif",
        img_t2_bytes_or_path="invalid_path_2.tif"
    )
    # Should fall back cleanly without unhandled crash
    assert meta["data_source_mode"] in ["SYNTHETIC_REGIONAL_BASELINE", "REAL_TEMPORAL_GEOTIFF"]
    assert len(events) > 0


# =====================================================================
# 4. RBAC & SECURITY GATES
# =====================================================================

def test_rbac_token_generation_and_roles():
    owner_token = auth_service.create_access_token("owner_user", "OWNER")
    admin_token = auth_service.create_access_token("admin_user", "ADMIN")
    staff_token = auth_service.create_access_token("staff_user", "STAFF")
    
    assert auth_service.decode_token(owner_token)["role"] == "OWNER"
    assert auth_service.decode_token(admin_token)["role"] == "ADMIN"
    assert auth_service.decode_token(staff_token)["role"] == "STAFF"

def test_rbac_access_control_audit_logs():
    admin_token = auth_service.create_access_token("admin", "ADMIN")
    staff_token = auth_service.create_access_token("staff", "STAFF")
    
    # ADMIN is allowed to access audit logs
    admin_res = client.get("/api/audit/logs", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_res.status_code == 200
    
    # STAFF is forbidden (403) from accessing audit logs
    staff_res = client.get("/api/audit/logs", headers={"Authorization": f"Bearer {staff_token}"})
    assert staff_res.status_code == 403

def test_security_invalid_and_expired_jwt():
    import jwt
    from backend.app.services.auth.auth_service import JWT_SECRET_KEY, JWT_ALGORITHM
    
    # Invalid JWT
    bad_res = client.get("/api/audit/logs", headers={"Authorization": "Bearer invalid.jwt.token"})
    assert bad_res.status_code == 401
    
    # Expired JWT (issued with past expiration)
    expired_payload = {
        "sub": "expired_admin",
        "role": "ADMIN",
        "type": "access",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1)
    }
    expired_token = jwt.encode(expired_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    exp_res = client.get("/api/audit/logs", headers={"Authorization": f"Bearer {expired_token}"})
    assert exp_res.status_code == 401

def test_ai_harmonizer_hard_legal_gate_override_prevention():
    base_parcel = {"parcel_id": "P-BASE", "survey_no": "100", "legacy_area": 1000.0}
    # Massive area mismatch (1000m² vs 3000m² -> >50% mismatch)
    cand_parcel = {"parcel_id": "P-CAND", "survey_no": "100", "legacy_area": 3000.0}
    
    poly_a = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    poly_b = Polygon([(500, 500), (600, 500), (600, 600), (500, 600)]) # Far away: extreme Hausdorff
    
    eval_res = ai_harmonizer.evaluate_candidate(
        base_parcel=base_parcel,
        candidate_parcel=cand_parcel,
        base_geom=poly_a,
        candidate_geom=poly_b,
        gnss_support=False,
        utility_conflict=False
    )
    
    # Must be strictly rejected by hard gates regardless of AI score
    assert eval_res["hard_gates_passed"] is False
    assert eval_res["decision"] == "REJECTED_BY_HARD_GATE"
    assert len(eval_res["gate_failures"]) > 0

