"""
ULAG Assisted Shared-Boundary Resolution & Slicing Service
Provides candidate topology splits for overlapping cadastral parcels, calculates area deltas,
and enforces human approval workflows before updating legal geometries.
"""

from typing import Dict, Any, List, Optional, Tuple
import uuid
from datetime import datetime, timezone
from shapely.geometry import Polygon, MultiPolygon, shape, mapping, LineString
from shapely.ops import split, unary_union

try:
    from backend.app.models.storage import storage_repo
except ImportError:
    from app.models.storage import storage_repo


class SharedBoundarySlicer:
    """
    Computes assisted shared-boundary resolutions for overlapping or conflicting parcels.
    Ensures strict human-in-the-loop review: candidate splits are proposed and previewed,
    never committed without explicit human approval.
    """

    def propose_split(
        self,
        parcel_a_id: str,
        parcel_b_id: str,
        geom_a_geojson: Dict[str, Any],
        geom_b_geojson: Dict[str, Any],
        operator: str = "admin",
        split_strategy: str = "MEDIAL_AXIS_BISECTOR" # Options: "MEDIAL_AXIS_BISECTOR", "EQUAL_AREA_DIVIDE", "PRIORITIZE_A", "PRIORITIZE_B"
    ) -> Dict[str, Any]:
        """
        Calculates an overlapping sliver/conflict between parcel A and B, generates candidate
        split geometries, computes area before/after, and registers a proposal.
        """
        geom_a = shape(geom_a_geojson)
        geom_b = shape(geom_b_geojson)

        if not geom_a.is_valid:
            geom_a = geom_a.buffer(0)
        if not geom_b.is_valid:
            geom_b = geom_b.buffer(0)

        overlap = geom_a.intersection(geom_b)
        overlap_area = overlap.area

        if overlap_area <= 0.001:
            return {
                "success": False,
                "message": "Parcels do not overlap or overlap is negligible (< 0.001 m2)."
            }

        area_a_before = geom_a.area
        area_b_before = geom_b.area

        # Compute candidate resolved geometries based on strategy
        if split_strategy == "PRIORITIZE_A":
            # Parcel A keeps full geometry; Parcel B has overlap subtracted
            resolved_a = geom_a
            resolved_b = geom_b.difference(geom_a)
        elif split_strategy == "PRIORITIZE_B":
            # Parcel B keeps full geometry; Parcel A has overlap subtracted
            resolved_a = geom_a.difference(geom_b)
            resolved_b = geom_b
        else: # "MEDIAL_AXIS_BISECTOR" or "EQUAL_AREA_DIVIDE" (split overlap in half)
            # Bisect the overlap bounding box or centroid line
            overlap_centroid = overlap.centroid
            # Cut overlap geometry across centroid horizontally or along principal direction
            minx, miny, maxx, maxy = overlap.bounds
            mid_x = (minx + maxx) / 2.0
            mid_y = (miny + maxy) / 2.0

            # If wider than tall, split vertically; else split horizontally
            if (maxx - minx) >= (maxy - miny):
                divider = LineString([(mid_x, miny - 10), (mid_x, maxy + 10)])
            else:
                divider = LineString([(minx - 10, mid_y), (maxx + 10, mid_y)])

            split_pieces = list(split(overlap, divider).geoms) if hasattr(split(overlap, divider), 'geoms') else [overlap]
            
            if len(split_pieces) >= 2:
                piece_1 = split_pieces[0]
                piece_2 = unary_union(split_pieces[1:])
            else:
                piece_1 = overlap
                piece_2 = Polygon()

            # Assign piece_1 to A and piece_2 to B
            diff_a = geom_a.difference(overlap)
            diff_b = geom_b.difference(overlap)
            resolved_a = unary_union([diff_a, piece_1])
            resolved_b = unary_union([diff_b, piece_2])

        area_a_after = resolved_a.area
        area_b_after = resolved_b.area

        proposal_id = f"split-{uuid.uuid4().hex[:8]}"
        created_at = datetime.now(timezone.utc).isoformat()

        proposal_data = {
            "proposal_id": proposal_id,
            "parcel_a_id": parcel_a_id,
            "parcel_b_id": parcel_b_id,
            "split_strategy": split_strategy,
            "overlap_area_m2": round(overlap_area, 3),
            "area_a_before_m2": round(area_a_before, 3),
            "area_a_after_m2": round(area_a_after, 3),
            "delta_a_m2": round(area_a_after - area_a_before, 3),
            "area_b_before_m2": round(area_b_before, 3),
            "area_b_after_m2": round(area_b_after, 3),
            "delta_b_m2": round(area_b_after - area_b_before, 3),
            "original_geom_a": mapping(geom_a),
            "original_geom_b": mapping(geom_b),
            "proposed_geom_a": mapping(resolved_a),
            "proposed_geom_b": mapping(resolved_b),
            "status": "PENDING_REVIEW", # "PENDING_REVIEW", "APPROVED", "REJECTED"
            "created_by": operator,
            "created_at": created_at,
            "decided_by": None,
            "decided_at": None,
            "decision_notes": ""
        }

        storage_repo.save_shared_boundary_proposal(proposal_id, proposal_data)

        # Audit proposal creation
        storage_repo.save_audit_log(
            user_id=operator,
            action="PROPOSE_BOUNDARY_SPLIT",
            target_type="PARCEL_PAIR",
            target_id=f"{parcel_a_id}:{parcel_b_id}",
            details={
                "proposal_id": proposal_id,
                "strategy": split_strategy,
                "overlap_area_m2": overlap_area
            }
        )

        return proposal_data

    def decide_proposal(
        self,
        proposal_id: str,
        decision: str, # "APPROVED" or "REJECTED"
        operator: str = "admin",
        notes: str = ""
    ) -> Dict[str, Any]:
        """Human approval or rejection of boundary split proposal."""
        existing = storage_repo.get_shared_boundary_proposal(proposal_id)
        if not existing:
            raise ValueError(f"Proposal {proposal_id} not found.")

        if decision not in ["APPROVED", "REJECTED"]:
            raise ValueError("Decision must be either 'APPROVED' or 'REJECTED'.")

        updates = {
            "status": decision,
            "decided_by": operator,
            "decided_at": datetime.now(timezone.utc).isoformat(),
            "decision_notes": notes
        }

        storage_repo.update_shared_boundary_proposal(proposal_id, updates)

        # Audit decision
        storage_repo.save_audit_log(
            user_id=operator,
            action=f"{decision}_BOUNDARY_SPLIT",
            target_type="BOUNDARY_PROPOSAL",
            target_id=proposal_id,
            details={
                "parcel_a": existing.get("parcel_a_id"),
                "parcel_b": existing.get("parcel_b_id"),
                "notes": notes
            }
        )

        return {**existing, **updates}


shared_boundary_slicer = SharedBoundarySlicer()
