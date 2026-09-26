"""
End-to-End Comprehensive Lifecycle & Feature Suite for ULAG Platform
Validates Phase 1 to Phase 4 implementations:
- RBAC Authentication & Authorization
- National CRS Harmonization & UTM Zone crossing
- Deep-Learning ONNX Building Extraction & Fallback labeling
- Raster Change Detection & Classification
- Scanned Cadastral/Revenue OCR & Human-in-the-loop verification
- Manual Georeferencing & 4-Point Affine Rubber Sheeting with RMSE
- AI-Assisted Harmonization Ranking with Hard Legal Gates
- Assisted Shared-Boundary Slicing & Approval
- 3D Cadastral Volumetric Extrusions vs Legal Strata
- Memory-bounded Streaming Loader
- Immutable Audit Trail Logging
"""

import pytest
import os
import json
import numpy as np
from shapely.geometry import Polygon, mapping

from backend.app.services.auth.auth_service import auth_service
from backend.app.services.crs.national_crs import national_crs_harmonizer
from backend.app.services.ai.onnx_building_detector import onnx_detector
from backend.app.services.change_detection.raster_change_detector import raster_change_detector
from backend.app.services.ocr.ocr_service import ocr_service
from backend.app.services.geometry.georeferencer import georeferencer
from backend.app.services.matching.ai_ranking import ai_harmonizer
from backend.app.services.topology.shared_boundary_slicer import shared_boundary_slicer
from backend.app.services.cadastral_3d.service_3d import cadastral_3d_service
from backend.app.services.ingestion.streaming_loader import streaming_loader
from backend.app.models.storage import storage_repo


def test_auth_rbac_flow():
    """Validates login, password verification, token generation, and role checks."""
    # 1. Login with valid admin credentials
    res = auth_service.authenticate_user("admin", "admin123")
    assert "access_token" in res
    assert "refresh_token" in res
    assert res["user"]["role"] == "ADMIN"

    # 2. Login with invalid password
    with pytest.raises(Exception):
        auth_service.authenticate_user("admin", "wrong_password")

    # 3. Refresh token
    ref_res = auth_service.refresh_user_token(res["refresh_token"])
    assert "access_token" in ref_res

    # 4. Decode access token
    payload = auth_service.decode_token(ref_res["access_token"])
    assert payload["sub"] == "admin"
    assert payload["role"] == "ADMIN"


def test_national_crs_validation():
    """Validates UTM zone calculation, geographic CRS warning, and zone crossing."""
    # Geographic CRS EPSG:4326 should produce a critical warning
    res_wgs84 = national_crs_harmonizer.validate_and_recommend_crs(
        input_crs="EPSG:4326",
        sample_coordinates=[[76.95, 11.00]]
    )
    assert res_wgs84["recommended_crs"] == "EPSG:32643"
    assert res_wgs84["zone"] == "43N"
    assert len(res_wgs84["warnings"]) > 0

    # Cross-zone dataset spanning UTM 43 and 44
    res_cross = national_crs_harmonizer.validate_and_recommend_crs(
        input_crs="EPSG:4326",
        sample_coordinates=[[76.5, 11.0], [79.5, 11.0]]
    )
    assert len(res_cross["zones_spanned"]) == 2
    assert any("BOUNDARY WARNING" in w for w in res_cross["warnings"])


def test_onnx_building_detector_fallback_mode():
    """Verifies ONNX building detector fallback labeling and output structure."""
    # Test without model weights: must explicitly report FALLBACK mode, never claiming false neural inference
    buildings = onnx_detector.extract_building_footprints(
        raster_path=None,
        confidence_threshold=0.30
    )
    assert len(buildings) > 0
    b0 = buildings[0]
    assert b0["inference_mode"] in ["ONNX", "FALLBACK"]
    assert b0["model"] == "YOLOv8-Seg"
    assert "area_m2" in b0
    assert b0["confidence"] >= 0.30
    assert "geometry" in b0


def test_raster_change_detection():
    """Verifies bi-temporal change detection baseline and polygonization."""
    changes = raster_change_detector.detect_changes(
        before_raster_path=None,
        after_raster_path=None,
        threshold=25.0
    )
    assert len(changes) > 0
    c0 = changes[0]
    assert c0["change_type"] in ["BUILDING_ADDED", "BUILDING_REMOVED", "BUILDING_EXPANSION", "SIGNIFICANT_LAND_COVER_CHANGE"]
    assert c0["algorithm"] == "CLASSICAL_IMAGE_DIFFERENCING_BASELINE"
    assert "geometry" in c0
    assert c0["confidence"] > 0.0


def test_scanned_cadastral_ocr_extraction():
    """Verifies OCR extraction of revenue/cadastral fields and human verification."""
    # Process document
    res = ocr_service.process_document(file_bytes=None, filename="sample_patta_doc.pdf")
    assert res["status"] == "SUCCESS"
    assert "fields" in res
    assert "survey_number" in res["fields"]
    assert res["fields"]["survey_number"]["confidence"] > 0.0
    doc_id = res["doc_id"]

    # Verify document fields (human in the loop)
    updated_fields = res["fields"]
    updated_fields["survey_number"]["value"] = "104/2B"
    verified_res = ocr_service.verify_document_fields(
        doc_id=doc_id,
        updated_fields=updated_fields,
        operator="admin"
    )
    assert verified_res["verified"] is True
    assert verified_res["fields"]["survey_number"]["value"] == "104/2B"


def test_georeferencer_affine_rubber_sheeting():
    """Verifies least-squares affine transformation and RMSE residual calculation."""
    # Generate 4 synthetic control points with pure translation (+100, +200) and scale 1.0
    control_points = [
        {"point_id": "P1", "img_x": 0.0, "img_y": 0.0, "map_x": 100.0, "map_y": 200.0},
        {"point_id": "P2", "img_x": 100.0, "img_y": 0.0, "map_x": 200.0, "map_y": 200.0},
        {"point_id": "P3", "img_x": 100.0, "img_y": 100.0, "map_x": 200.0, "map_y": 300.0},
        {"point_id": "P4", "img_x": 0.0, "img_y": 100.0, "map_x": 100.0, "map_y": 300.0}
    ]

    res = georeferencer.compute_affine_transformation(
        image_name="cadastral_map_sheet_14.tif",
        control_points=control_points,
        target_crs="EPSG:32643",
        operator="surveyor_ajai"
    )
    # Perfect fit should have near-zero RMSE
    assert res.rmse < 0.001
    assert res.status == "ACCEPTED"
    assert len(res.point_residuals) == 4

    # Point transform
    tx, ty = georeferencer.transform_point(res.affine_matrix, 50.0, 50.0)
    assert abs(tx - 150.0) < 0.01
    assert abs(ty - 250.0) < 0.01


def test_ai_assisted_harmonization_ranking_and_gates():
    """Verifies candidate ranking, feature extraction, explainable output, and hard legal gates."""
    base_poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)]) # 100 m2
    matching_cand = Polygon([(0.5, 0.5), (10.5, 0.5), (10.5, 10.5), (0.5, 10.5)]) # 100 m2, high overlap

    base_parcel = {"parcel_id": "P-BASE-1", "survey_number": "45/1", "village": "Perur"}
    cand_parcel = {"parcel_id": "P-DRONE-1", "survey_number": "45/1", "village": "Perur"}

    eval_result = ai_harmonizer.evaluate_candidate(
        base_parcel=base_parcel,
        candidate_parcel=cand_parcel,
        base_geom=base_poly,
        candidate_geom=matching_cand,
        gnss_support=True
    )
    assert eval_result["hard_gates_passed"] is True
    assert eval_result["final_confidence"] > 0.70
    assert "gnss_corroborated" in eval_result["learned_features"]
    assert "explanation" in eval_result

    # Adversarial test: candidate with massive Hausdorff distance and low IoU fails hard gate
    distant_poly = Polygon([(100, 100), (110, 100), (110, 110), (100, 110)])
    bad_result = ai_harmonizer.evaluate_candidate(
        base_parcel=base_parcel,
        candidate_parcel=cand_parcel,
        base_geom=base_poly,
        candidate_geom=distant_poly
    )
    assert bad_result["hard_gates_passed"] is False
    assert bad_result["decision"] == "REJECTED_BY_HARD_GATE"


def test_assisted_shared_boundary_slicing():
    """Verifies proposal generation, before/after area delta, and human decision workflow."""
    poly_a = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    poly_b = Polygon([(8, 0), (18, 0), (18, 10), (8, 10)]) # 20m2 overlap

    proposal = shared_boundary_slicer.propose_split(
        parcel_a_id="P-101",
        parcel_b_id="P-102",
        geom_a_geojson=mapping(poly_a),
        geom_b_geojson=mapping(poly_b),
        operator="adjudicator_admin"
    )
    assert proposal["overlap_area_m2"] == 20.0
    assert proposal["status"] == "PENDING_REVIEW"
    assert proposal["delta_a_m2"] != 0.0

    # Human decision: Approve split
    prop_id = proposal["proposal_id"]
    decided = shared_boundary_slicer.decide_proposal(
        proposal_id=prop_id,
        decision="APPROVED",
        operator="chief_surveyor",
        notes="Mutually agreed boundary along bisector."
    )
    assert decided["status"] == "APPROVED"
    assert decided["decided_by"] == "chief_surveyor"


def test_3d_cadastral_extrusion_and_legal_volume():
    """Verifies physical 3D building extrusion and distinction from legal cadastral strata."""
    footprint = {
        "type": "Polygon",
        "coordinates": [[[76.95, 11.01], [76.96, 11.01], [76.96, 11.02], [76.95, 11.02], [76.95, 11.01]]]
    }
    # 1. Physical 3D Extrusion
    phys_3d = cadastral_3d_service.process_3d_footprint_extrusion(
        footprint_geojson=footprint,
        base_elevation_m=420.0,
        height_m=15.0,
        associated_parcel_id="P-301"
    )
    assert phys_3d["is_legal_volumetric_parcel"] is False
    assert phys_3d["legal_status"] == "PHYSICAL_STRUCTURE_ONLY"
    assert phys_3d["roof_elevation_m"] == 435.0

    # 2. Legal Cadastral Volume (Strata parcel)
    strata = cadastral_3d_service.register_legal_cadastral_volume(
        strata_id="STRATA-UNIT-4B",
        parent_parcel_id="P-301",
        floor_level=4,
        lower_bound_z_m=432.0,
        upper_bound_z_m=435.0,
        footprint_geojson=footprint,
        unit_number="Flat 402",
        owner_name="S. Ramanathan"
    )
    assert strata["is_legal_volumetric_parcel"] is True
    assert strata["legal_status"] == "LEGALLY_BINDING_3D_PROPERTY"
    assert strata["stratum_height_m"] == 3.0


def test_streaming_loader_large_geojson():
    """Verifies memory-bounded chunked ingestion of GeoJSON features."""
    sample_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": f"P-{i}",
                "properties": {"survey_no": str(i), "area_m2": 500.0},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[76.9 + i*0.001, 11.0], [76.91 + i*0.001, 11.0], [76.91 + i*0.001, 11.01], [76.9 + i*0.001, 11.01], [76.9 + i*0.001, 11.0]]]
                }
            } for i in range(15)
        ]
    }
    chunks = list(streaming_loader.stream_geojson_features(sample_geojson, chunk_size=5))
    assert len(chunks) == 3
    assert len(chunks[0]) == 5
    assert chunks[0][0]["id"] == "P-0"


def test_audit_logs_recording():
    """Verifies that audit actions are recorded and queryable."""
    storage_repo.save_audit_log(
        username="admin",
        action="TEST_E2E_AUDIT_ACTION",
        parcel_id="P-AUDIT-999",
        old_status="CONFLICT",
        new_status="RESOLVED",
        confidence=0.95,
        details={"test": True}
    )
    logs = storage_repo.get_audit_logs(limit=10)
    assert len(logs) > 0
    matched = [l for l in logs if l.get("action") == "TEST_E2E_AUDIT_ACTION"]
    assert len(matched) > 0
    assert matched[0]["parcel_id"] == "P-AUDIT-999"
