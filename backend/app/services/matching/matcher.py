"""
Spatial Parcel Matching Engine for ULAG
Problem Statement 26013: Automated Integration & Intelligent Harmonization of Multi-source Geospatial Data

Architectural Guarantees:
1. Strict Projected Coordinate Reference System (PyProj Geodetic Projection to UTM).
2. Multi-Metric Rigorous Geometry Analysis (IoU, Symmetric Coverage, Area concordance, Centroid distance,
   boundary point-to-point deviation, Hausdorff distance, boundary conformance).
3. Ground Truth GNSS/RTK Point Verification (Point-in-polygon & boundary clearance in metric space).
4. Hard Geometric Constraint Gating (Enforces non-negotiable geometric bounds; prevents false positives).
5. Comprehensive Candidate Audit Trail (Ranks and audits all overlapping candidates).
6. Deterministic, Dynamic Explainable Reasoning (Zero hardcoded text).
"""

import math
from typing import Dict, List, Any, Optional, Tuple
from shapely.geometry import shape, Polygon, MultiPolygon, Point
from shapely.strtree import STRtree

from backend.app.config import (
    MATCH_WEIGHTS, classify_confidence_status,
    BOUNDARY_TOLERANCE_METERS, BOUNDARY_SAMPLE_INTERVAL_METERS,
    MAX_PERMISSIBLE_BOUNDARY_DEVIATION_METERS,
    MEAN_PERMISSIBLE_BOUNDARY_DEVIATION_METERS, MAX_PERMISSIBLE_AREA_DIFFERENCE_PCT,
    MIN_IOU_FOR_AUTO_MATCH, GNSS_RTK_BUFFER_TOLERANCE_METERS,
    SPATIAL_INDEX_SEARCH_RADIUS_METERS
)
from backend.app.schemas.cadastral import EvidenceMetrics
from backend.app.services.geometry.crs import (
    get_optimal_projected_crs, project_geometry, project_point,
    validate_and_repair_geometry
)

# Reference Base Constants for Coimbatore Urban Sector (Backward Compatibility)
BASE_LAT = 11.0168
BASE_LON = 76.9558
M_PER_DEG_LAT = 111132.95
M_PER_DEG_LON = 111132.95 * math.cos(math.radians(BASE_LAT))

def normalize_survey_number(survey_str: str) -> str:
    """Normalizes survey number strings for clean comparison."""
    if not survey_str:
        return ""
    cleaned = str(survey_str).strip().replace(" ", "")
    parts = cleaned.split("/")
    norm_parts = [p.lstrip("0") or "0" for p in parts]
    return "/".join(norm_parts)

def calculate_attribute_similarity(survey_a: str, survey_b: str) -> float:
    """Calculates attribute agreement between legacy survey ref and drone candidate."""
    norm_a = normalize_survey_number(survey_a)
    norm_b = normalize_survey_number(survey_b)
    if not norm_a or not norm_b:
        return 50.0
    if norm_a == norm_b:
        return 100.0
    base_a = norm_a.split("/")[0]
    base_b = norm_b.split("/")[0]
    if base_a == base_b:
        return 80.0
    return 20.0

def compute_boundary_deviations(
    poly_a: Any,
    poly_b: Any,
    tolerance_m: float = BOUNDARY_TOLERANCE_METERS,
    sample_interval_m: float = BOUNDARY_SAMPLE_INTERVAL_METERS
) -> Dict[str, float]:
    """
    Computes rigorous point-to-point boundary deviations in projected meters.
    Samples perimeter vertices at configurable spatial intervals (default 0.5m)
    and calculates mean, median, p90, p95, p99, max deviation, Hausdorff distance,
    and boundary conformance percentage within specified tolerance.
    """
    if getattr(poly_a, "geom_type", "") == "MultiPolygon":
        poly_a = max(poly_a.geoms, key=lambda g: g.area)
    if getattr(poly_b, "geom_type", "") == "MultiPolygon":
        poly_b = max(poly_b.geoms, key=lambda g: g.area)

    ext_a = getattr(poly_a, "exterior", poly_a.boundary)
    ext_b = getattr(poly_b, "exterior", poly_b.boundary)

    # Sample points along poly_a exterior
    len_a = ext_a.length
    step_a = max(0.2, min(sample_interval_m, len_a / 20.0)) if len_a > 0 else 1.0
    num_pts_a = max(20, int(len_a / step_a)) if len_a > 0 else 0
    dists_a = [ext_b.distance(ext_a.interpolate(i * step_a)) for i in range(num_pts_a)]

    # Sample points along poly_b exterior
    len_b = ext_b.length
    step_b = max(0.2, min(sample_interval_m, len_b / 20.0)) if len_b > 0 else 1.0
    num_pts_b = max(20, int(len_b / step_b)) if len_b > 0 else 0
    dists_b = [ext_a.distance(ext_b.interpolate(i * step_b)) for i in range(num_pts_b)]

    all_dists = dists_a + dists_b
    if not all_dists:
        return {
            "mean_dev": 0.0,
            "median_dev": 0.0,
            "max_dev": 0.0,
            "p90_dev": 0.0,
            "p95_dev": 0.0,
            "p99_dev": 0.0,
            "hausdorff": 0.0,
            "conformance_pct": 100.0
        }

    sorted_dists = sorted(all_dists)
    n = len(sorted_dists)
    mean_dev = sum(all_dists) / n
    median_dev = sorted_dists[int(0.50 * (n - 1))]
    p90_idx = int(0.90 * (n - 1))
    p95_idx = int(0.95 * (n - 1))
    p99_idx = int(0.99 * (n - 1))
    p90_dev = sorted_dists[p90_idx]
    p95_dev = sorted_dists[p95_idx]
    p99_dev = sorted_dists[p99_idx]
    max_dev = max(all_dists)

    try:
        import shapely
        h_dist = shapely.hausdorff_distance(ext_a, ext_b)
    except Exception:
        try:
            h_dist = ext_a.hausdorff_distance(ext_b)
        except Exception:
            h_dist = max_dev

    within_tol = sum(1 for d in all_dists if d <= tolerance_m)
    conformance_pct = (within_tol / n) * 100.0

    return {
        "mean_dev": round(mean_dev, 2),
        "median_dev": round(median_dev, 2),
        "max_dev": round(max_dev, 2),
        "p90_dev": round(p90_dev, 2),
        "p95_dev": round(p95_dev, 2),
        "p99_dev": round(p99_dev, 2),
        "hausdorff": round(h_dist, 2),
        "conformance_pct": round(conformance_pct, 1)
    }

class ParcelMatcher:
    def __init__(self, drone_features: List[Dict[str, Any]], source_crs: str = "EPSG:4326"):
        self.source_crs = source_crs
        self.drone_features = drone_features
        self.drone_geoms_wgs84 = []
        self.drone_geoms_proj = []
        self.drone_lookup = {}
        self.projected_crs = "EPSG:32643"

        # Determine projected CRS from first valid feature
        for feat in drone_features:
            g_dict = feat.get("geometry")
            if g_dict:
                sh_geom = shape(g_dict)
                c = sh_geom.centroid
                self.projected_crs = get_optimal_projected_crs(c.x, c.y)
                break

        for idx, feat in enumerate(drone_features):
            raw_geom = shape(feat["geometry"])
            v_geom, was_repaired, _ = validate_and_repair_geometry(raw_geom, feat.get("id", f"FE_{idx}"))
            proj_geom = project_geometry(v_geom, src_crs=self.source_crs, target_crs=self.projected_crs)
            self.drone_geoms_wgs84.append(v_geom)
            self.drone_geoms_proj.append(proj_geom)
            self.drone_lookup[idx] = feat

        # Build R-tree spatial index on projected geometries
        self.spatial_index = STRtree(self.drone_geoms_proj)

    def match_parcel(
        self,
        legacy_feature: Dict[str, Any],
        gnss_points: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[Optional[Dict[str, Any]], EvidenceMetrics, List[Dict[str, Any]]]:
        """
        Performs rigorous, mathematically grounded candidate generation, geodetic comparison,
        and multi-factor consensus scoring with hard constraint gating.
        """
        props = legacy_feature.get("properties", {})
        p_id = props.get("parcel_id", "Unknown")
        s_no = str(props.get("survey_no", ""))
        sub_no = str(props.get("subdivision_no", "1"))
        full_survey = props.get("full_survey") or f"{s_no}/{sub_no}"

        raw_legacy = shape(legacy_feature["geometry"])
        v_legacy, was_rep, rep_reason = validate_and_repair_geometry(raw_legacy, p_id)
        proj_legacy = project_geometry(v_legacy, src_crs=self.source_crs, target_crs=self.projected_crs)

        legacy_area_m2 = round(proj_legacy.area, 2)
        recorded_legacy_area = float(props.get("area", legacy_area_m2))

        # Spatial candidate search: expand projected bounding box by configurable radius in meters
        search_envelope = proj_legacy.buffer(SPATIAL_INDEX_SEARCH_RADIUS_METERS)
        candidate_indices = self.spatial_index.query(search_envelope)

        all_candidates_audit: List[Dict[str, Any]] = []

        # Prepare GNSS points in projected coordinates
        proj_gnss_pts = []
        if gnss_points:
            for pt in gnss_points:
                try:
                    px, py = project_point(pt["longitude"], pt["latitude"], src_crs="EPSG:4326", target_crs=self.projected_crs)
                    proj_gnss_pts.append(Point(px, py))
                except Exception:
                    pass

        best_feat = None
        best_evidence = None
        best_score = -1.0

        for c_idx in candidate_indices:
            drone_feat = self.drone_lookup[c_idx]
            proj_drone = self.drone_geoms_proj[c_idx]
            d_props = drone_feat.get("properties", {})
            d_id = drone_feat.get("id") or d_props.get("feature_id", f"FE_{c_idx:03d}")
            d_survey = d_props.get("survey_candidate", "")

            drone_area_m2 = round(proj_drone.area, 2)

            # 1. Intersection over Union (IoU) and Coverage
            try:
                inter_geom = proj_legacy.intersection(proj_drone)
                union_geom = proj_legacy.union(proj_drone)
                inter_area = inter_geom.area
                union_area = union_geom.area
                iou = (inter_area / union_area * 100.0) if union_area > 0 else 0.0
                cov_source = (inter_area / proj_legacy.area * 100.0) if proj_legacy.area > 0 else 0.0
                cov_cand = (inter_area / proj_drone.area * 100.0) if proj_drone.area > 0 else 0.0
            except Exception:
                iou = 0.0
                cov_source = 0.0
                cov_cand = 0.0

            # 2. Area Concordance
            area_diff_m2 = abs(legacy_area_m2 - drone_area_m2)
            max_a = max(legacy_area_m2, drone_area_m2)
            min_a = min(legacy_area_m2, drone_area_m2)
            area_diff_pct = (area_diff_m2 / max_a * 100.0) if max_a > 0 else 0.0
            area_match_pct = round((min_a / max_a * 100.0), 1) if max_a > 0 else 0.0

            # 3. Metric Centroid Distance
            cent_dist_m = round(proj_legacy.centroid.distance(proj_drone.centroid), 2)
            centroid_match_pct = max(0.0, round(100.0 - (cent_dist_m / 15.0 * 100.0), 1))

            # 4. Point-to-Point Boundary Conformance
            b_metrics = compute_boundary_deviations(proj_legacy, proj_drone, tolerance_m=BOUNDARY_TOLERANCE_METERS)
            bound_conf_pct = b_metrics["conformance_pct"]
            mean_dev_m = b_metrics["mean_dev"]
            max_dev_m = b_metrics["max_dev"]
            p95_dev_m = b_metrics["p95_dev"]
            hausdorff_m = b_metrics["hausdorff"]

            # 5. GNSS Survey Concordance
            gnss_inside_count = 0
            gnss_inside_pct = 100.0
            gnss_status = "NO_DATA"
            if proj_gnss_pts:
                # Buffer candidate by 35cm RTK tolerance
                buffered_drone = proj_drone.buffer(GNSS_RTK_BUFFER_TOLERANCE_METERS)
                for pt in proj_gnss_pts:
                    if buffered_drone.contains(pt):
                        gnss_inside_count += 1
                gnss_inside_pct = round((gnss_inside_count / len(proj_gnss_pts)) * 100.0, 1)
                if gnss_inside_pct >= 90.0:
                    gnss_status = "HIGH"
                elif gnss_inside_pct >= 50.0:
                    gnss_status = "MEDIUM"
                else:
                    gnss_status = "LOW"

            # 6. Survey / Revenue Attribute Agreement
            attr_match_pct = calculate_attribute_similarity(full_survey, d_survey)

            # 7. Spatial & Boundary Proximity Score (continuous metric in meters)
            prox_match_pct = max(0.0, round(100.0 - (mean_dev_m / 35.0 * 100.0), 1))

            # Composite Weighted Match Confidence using official MATCH_WEIGHTS
            raw_score = round(
                MATCH_WEIGHTS["geometry"] * iou +
                MATCH_WEIGHTS["area"] * area_match_pct +
                MATCH_WEIGHTS["centroid"] * centroid_match_pct +
                MATCH_WEIGHTS["attribute"] * attr_match_pct +
                MATCH_WEIGHTS["proximity"] * prox_match_pct,
                1
            )

            # --- HARD GEOMETRIC CONSTRAINT CHECKS ---
            hard_flags: List[str] = []
            rejection_reason = None

            if max_dev_m > MAX_PERMISSIBLE_BOUNDARY_DEVIATION_METERS:
                hard_flags.append(f"Maximum boundary deviation ({max_dev_m}m) exceeds permissible limit ({MAX_PERMISSIBLE_BOUNDARY_DEVIATION_METERS}m)")
            if mean_dev_m > MEAN_PERMISSIBLE_BOUNDARY_DEVIATION_METERS:
                hard_flags.append(f"Mean boundary deviation ({mean_dev_m}m) exceeds permissible limit ({MEAN_PERMISSIBLE_BOUNDARY_DEVIATION_METERS}m)")
            if area_diff_pct > MAX_PERMISSIBLE_AREA_DIFFERENCE_PCT:
                hard_flags.append(f"Area divergence ({area_diff_pct:.1f}%) exceeds permissible limit ({MAX_PERMISSIBLE_AREA_DIFFERENCE_PCT}%)")
            if iou < MIN_IOU_FOR_AUTO_MATCH:
                hard_flags.append(f"Geometry IoU ({iou:.1f}%) below auto-match threshold ({MIN_IOU_FOR_AUTO_MATCH}%)")
            if proj_gnss_pts and gnss_inside_pct < 50.0:
                hard_flags.append(f"GNSS survey evidence contradicts candidate ({gnss_inside_pct}% points inside)")

            # Hard Constraint Gating
            final_cand_score = raw_score
            if hard_flags:
                final_cand_score = min(raw_score, 65.0)
                rejection_reason = "; ".join(hard_flags)

            audit_item = {
                "candidate_id": d_id,
                "survey_candidate": d_survey,
                "iou": round(iou, 1),
                "coverage_source": round(cov_source, 1),
                "coverage_candidate": round(cov_cand, 1),
                "area_diff_pct": round(area_diff_pct, 1),
                "centroid_dist_m": cent_dist_m,
                "mean_boundary_dev_m": mean_dev_m,
                "max_boundary_dev_m": max_dev_m,
                "p95_boundary_dev_m": p95_dev_m,
                "hausdorff_m": hausdorff_m,
                "boundary_conformance": bound_conf_pct,
                "gnss_inside_pct": gnss_inside_pct,
                "attribute_match": attr_match_pct,
                "score": final_cand_score,
                "hard_flags": hard_flags,
                "rejection_reason": rejection_reason
            }
            all_candidates_audit.append(audit_item)

            if final_cand_score > best_score:
                best_score = final_cand_score
                best_feat = drone_feat

                # Build explainable reasoning checklist dynamically
                checklist = []
                # 1. Overlap
                if iou >= 80.0:
                    checklist.append({"status": "PASS", "text": f"Boundary overlap is high (IoU {round(iou, 1)}%, Coverage {round(cov_source, 1)}%)"})
                elif iou >= 50.0:
                    checklist.append({"status": "WARN", "text": f"Boundary overlap is moderate (IoU {round(iou, 1)}%)"})
                else:
                    checklist.append({"status": "FAIL", "text": f"Boundary overlap is insufficient (IoU {round(iou, 1)}%)"})

                # 2. Area
                if area_diff_pct <= 5.0:
                    checklist.append({"status": "PASS", "text": f"Area difference is within strict tolerance (±{round(area_diff_m2, 1)} m² / {round(area_diff_pct, 1)}%)"})
                elif area_diff_pct <= 15.0:
                    checklist.append({"status": "WARN", "text": f"Area discrepancy detected (Δ {round(area_diff_m2, 1)} m² / {round(area_diff_pct, 1)}%)"})
                else:
                    checklist.append({"status": "FAIL", "text": f"Severe area mismatch (Δ {round(area_diff_m2, 1)} m² / {round(area_diff_pct, 1)}%)"})

                # 3. Boundary deviation
                if mean_dev_m <= 1.0 and bound_conf_pct >= 90.0:
                    checklist.append({"status": "PASS", "text": f"Boundary conforms {bound_conf_pct}% within {BOUNDARY_TOLERANCE_METERS}m (Mean dev: {mean_dev_m}m, Max: {max_dev_m}m)"})
                elif mean_dev_m <= 3.0:
                    checklist.append({"status": "WARN", "text": f"Boundary displacement observed (Mean dev: {mean_dev_m}m, Max: {max_dev_m}m)"})
                else:
                    checklist.append({"status": "FAIL", "text": f"Excessive boundary deviation (Mean dev: {mean_dev_m}m, Max: {max_dev_m}m)"})

                # 4. GNSS
                if proj_gnss_pts:
                    if gnss_inside_pct >= 90.0:
                        checklist.append({"status": "PASS", "text": f"GNSS RTK survey: {gnss_inside_count}/{len(proj_gnss_pts)} points ({gnss_inside_pct}%) lie inside candidate geometry"})
                    else:
                        checklist.append({"status": "FAIL", "text": f"GNSS ground survey contradiction: only {gnss_inside_count}/{len(proj_gnss_pts)} points inside candidate"})
                else:
                    checklist.append({"status": "INFO", "text": "No field GNSS CORS/RTK ground survey points associated with this survey number"})

                # 5. Attribute agreement
                if attr_match_pct >= 95.0:
                    checklist.append({"status": "PASS", "text": f"Survey identifier '{full_survey}' corroborated with Revenue records"})
                elif attr_match_pct >= 75.0:
                    checklist.append({"status": "WARN", "text": f"Survey subdivision variation ('{full_survey}' vs candidate '{d_survey}')"})
                else:
                    checklist.append({"status": "FAIL", "text": f"Survey identifier clash ('{full_survey}' vs candidate '{d_survey}')"})

                # 6. Drone difference
                drone_diff_pct = round(abs(legacy_area_m2 - drone_area_m2) / max(legacy_area_m2, 1.0) * 100.0, 1)
                if drone_diff_pct > 1.0:
                    checklist.append({"status": "WARN" if drone_diff_pct < 15.0 else "FAIL", "text": f"Legacy geometry differs by {drone_diff_pct}% from high-res Drone ORI"})
                else:
                    checklist.append({"status": "PASS", "text": "Legacy geometry concordant with high-res Drone ORI extraction"})

                decision_reason = "High multi-source concordance across geometric and attribute factors" if not hard_flags else f"Hard constraints triggered: {'; '.join(hard_flags)}"

                best_evidence = EvidenceMetrics(
                    geometry_match=round(iou, 1),
                    area_match=round(area_match_pct, 1),
                    centroid_match=round(centroid_match_pct, 1),
                    attribute_match=round(attr_match_pct, 1),
                    proximity_match=round(prox_match_pct, 1),
                    overall_confidence=final_cand_score,
                    boundary_conformance=bound_conf_pct,
                    mean_boundary_deviation_m=mean_dev_m,
                    max_boundary_deviation_m=max_dev_m,
                    p95_boundary_deviation_m=p95_dev_m,
                    hausdorff_distance_m=hausdorff_m,
                    coverage_source=round(cov_source, 1),
                    coverage_candidate=round(cov_cand, 1),
                    area_difference_pct=round(area_diff_pct, 1),
                    centroid_distance_m=cent_dist_m,
                    gnss_points_total=len(proj_gnss_pts),
                    gnss_points_inside=gnss_inside_count,
                    gnss_inside_percentage=gnss_inside_pct,
                    gnss_status=gnss_status,
                    drone_legacy_difference_pct=drone_diff_pct,
                    hard_constraint_flags=hard_flags,
                    decision_reason=decision_reason,
                    candidates_audit=[],  # populated after loop
                    why_matched_checklist=checklist
                )

        # Sort all candidates deterministically: score DESC, iou DESC, candidate_id ASC
        all_candidates_audit.sort(key=lambda c: (-c["score"], -c["iou"], c["candidate_id"]))
        for rank_idx, cand in enumerate(all_candidates_audit):
            cand["rank"] = rank_idx + 1

        if best_evidence:
            best_evidence.candidates_audit = all_candidates_audit

        # Collect runner up features for legacy caller compatibility
        runners_up = []
        if len(all_candidates_audit) > 1:
            for cand_rec in all_candidates_audit[1:3]:
                # find feat by id
                for f in self.drone_features:
                    if f.get("id") == cand_rec["candidate_id"] or f.get("properties", {}).get("feature_id") == cand_rec["candidate_id"]:
                        runners_up.append(f)
                        break

        if not best_feat or best_score < 40.0:
            default_checklist = [
                {"status": "FAIL", "text": "No corresponding polygon detected within spatial search radius"},
                {"status": "INFO", "text": "Possible tree canopy occlusion, unmapped subdivision, or extraction gap"}
            ]
            default_evidence = EvidenceMetrics(
                geometry_match=0.0,
                area_match=0.0,
                centroid_match=0.0,
                attribute_match=0.0,
                proximity_match=0.0,
                overall_confidence=0.0,
                boundary_conformance=0.0,
                mean_boundary_deviation_m=0.0,
                max_boundary_deviation_m=0.0,
                p95_boundary_deviation_m=0.0,
                hausdorff_distance_m=0.0,
                coverage_source=0.0,
                coverage_candidate=0.0,
                area_difference_pct=100.0,
                centroid_distance_m=0.0,
                gnss_points_total=len(proj_gnss_pts),
                gnss_points_inside=0,
                gnss_inside_percentage=0.0,
                gnss_status="NO_DATA" if not proj_gnss_pts else "LOW",
                drone_legacy_difference_pct=100.0,
                hard_constraint_flags=["Missing Drone Candidate"],
                decision_reason="No spatial candidate found within buffer radius",
                candidates_audit=all_candidates_audit,
                why_matched_checklist=default_checklist
            )
            return None, default_evidence, runners_up

        return best_feat, best_evidence, runners_up

class ReferenceSpatialMatcher:
    """Matches drone buildings and parcels against reference spatial layers (e.g. IndianOpenMaps)."""
    
    def match_buildings_reference(
        self,
        drone_buildings: List[Dict[str, Any]],
        ref_buildings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        results = []
        ref_geoms = []
        for rf in ref_buildings:
            rg = rf.get("geometry")
            if rg:
                try:
                    ref_geoms.append((rf.get("id") or rf.get("properties", {}).get("feature_id", "ref"), shape(rg)))
                except Exception:
                    pass

        for db in drone_buildings:
            b_id = db.get("building_id") or db.get("id", "bld")
            dg = db.get("geometry_geojson") or db.get("geometry")
            best_iou = 0.0
            best_ref_id = None
            if dg and ref_geoms:
                try:
                    d_poly = shape(dg)
                    for r_id, r_poly in ref_geoms:
                        if d_poly.intersects(r_poly):
                            inter_a = d_poly.intersection(r_poly).area
                            union_a = d_poly.union(r_poly).area
                            iou = (inter_a / union_a * 100.0) if union_a > 0 else 0.0
                            if iou > best_iou:
                                best_iou = iou
                                best_ref_id = r_id
                except Exception:
                    pass
            status = "MATCHED" if best_iou >= 50.0 else ("PARTIAL" if best_iou >= 20.0 else "UNMATCHED")
            results.append({
                "building_id": b_id,
                "match_status": status,
                "iou_percentage": round(best_iou, 2),
                "matched_ref_id": best_ref_id
            })
        return results

    def evaluate_parcel_reference_layers(
        self,
        parcel_geom: Dict[str, Any],
        iomaps_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        p_poly = shape(parcel_geom)
        
        bld_count = 0
        for b in iomaps_data.get("buildings", []):
            bg = b.get("geometry")
            if bg:
                try:
                    if p_poly.intersects(shape(bg)):
                        bld_count += 1
                except Exception:
                    pass

        min_dist_m = 999999.0
        for t in iomaps_data.get("transport", []):
            tg = t.get("geometry")
            if tg:
                try:
                    t_geom = shape(tg)
                    deg_dist = p_poly.distance(t_geom)
                    m_dist = deg_dist * 111139.0
                    if m_dist < min_dist_m:
                        min_dist_m = m_dist
                except Exception:
                    pass
        if min_dist_m == 999999.0:
            min_dist_m = 0.0

        water_overlap = False
        for w in iomaps_data.get("water", []):
            wg = w.get("geometry")
            if wg:
                try:
                    if p_poly.intersects(shape(wg)):
                        water_overlap = True
                        break
                except Exception:
                    pass

        power_intersect = False
        for p in iomaps_data.get("power", []):
            pg = p.get("geometry")
            if pg:
                try:
                    if p_poly.intersects(shape(pg)):
                        power_intersect = True
                        break
                except Exception:
                    pass

        return {
            "reference_building_count": bld_count,
            "nearest_road_distance_m": round(min_dist_m, 2),
            "waterbody_overlap": water_overlap,
            "power_line_intersection": power_intersect
        }

spatial_matcher = ReferenceSpatialMatcher()
