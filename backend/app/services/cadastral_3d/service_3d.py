"""
ULAG 3D Cadastral Foundation Service
Handles 3D physical building geometries (CityGML LoD1/LoD2, IFC, 3D GeoJSON) and
distinguishes physical structures from legal cadastral volumetric property rights (strata units).
"""

from typing import Dict, Any, List, Optional, Tuple
import math
from datetime import datetime, timezone
import uuid


class Cadastral3DService:
    """
    Manages 3D geospatial entities, volumetric extrusions, and strata parcel definitions.
    Strictly separates 'Physical 3D Building' (e.g. DSM/LiDAR height, LoD1 extrusion)
    from 'Legal Cadastral Volume' (vertical ownership stratum, 3D property boundary).
    """

    def process_3d_footprint_extrusion(
        self,
        footprint_geojson: Dict[str, Any],
        base_elevation_m: float,
        height_m: float,
        building_id: Optional[str] = None,
        associated_parcel_id: Optional[str] = None,
        source_format: str = "3D_GEOJSON" # "3D_GEOJSON", "CITYGML_LOD1", "CITYGML_LOD2", "IFC"
    ) -> Dict[str, Any]:
        """
        Extrudes a 2D building footprint into a 3D physical building volume using DSM/DTM elevation.
        """
        b_id = building_id or f"b3d-{uuid.uuid4().hex[:8]}"
        top_elevation_m = base_elevation_m + height_m

        coords = footprint_geojson.get("coordinates", [])
        # Construct 3D polygon ring with Z values
        ring_3d_base = []
        ring_3d_top = []
        if coords and len(coords) > 0:
            outer = coords[0] if isinstance(coords[0][0], list) else coords
            for pt in outer:
                ring_3d_base.append([pt[0], pt[1], round(base_elevation_m, 2)])
                ring_3d_top.append([pt[0], pt[1], round(top_elevation_m, 2)])

        return {
            "building_3d_id": b_id,
            "associated_parcel_id": associated_parcel_id,
            "entity_type": "PHYSICAL_3D_BUILDING",
            "lod_level": "LoD1",
            "source_format": source_format,
            "base_elevation_m": round(base_elevation_m, 2),
            "height_m": round(height_m, 2),
            "roof_elevation_m": round(top_elevation_m, 2),
            "estimated_volume_m3": round(footprint_geojson.get("properties", {}).get("area_m2", 100.0) * height_m, 2),
            "footprint_2d": footprint_geojson,
            "coordinates_3d": {
                "base_ring": ring_3d_base,
                "roof_ring": ring_3d_top
            },
            "is_legal_volumetric_parcel": False,
            "legal_status": "PHYSICAL_STRUCTURE_ONLY",
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    def register_legal_cadastral_volume(
        self,
        strata_id: str,
        parent_parcel_id: str,
        floor_level: int,
        lower_bound_z_m: float,
        upper_bound_z_m: float,
        footprint_geojson: Dict[str, Any],
        unit_number: str,
        owner_name: str,
        tenure_type: str = "STRATA_FREEHOLD"
    ) -> Dict[str, Any]:
        """
        Registers a true 3D legal cadastral volume (stratum parcel / air rights / underground subway).
        """
        vol_height = upper_bound_z_m - lower_bound_z_m
        return {
            "strata_id": strata_id,
            "parent_parcel_id": parent_parcel_id,
            "entity_type": "LEGAL_CADASTRAL_VOLUME",
            "unit_number": unit_number,
            "owner_name": owner_name,
            "tenure_type": tenure_type,
            "floor_level": floor_level,
            "vertical_datum": "EGM2008_MSL",
            "lower_bound_z_m": round(lower_bound_z_m, 2),
            "upper_bound_z_m": round(upper_bound_z_m, 2),
            "stratum_height_m": round(vol_height, 2),
            "is_legal_volumetric_parcel": True,
            "legal_status": "LEGALLY_BINDING_3D_PROPERTY",
            "geometry_boundaries_3d": footprint_geojson,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    def generate_demo_3d_buildings(self) -> List[Dict[str, Any]]:
        """Generates representative 3D building models for WebGIS 3D visualization demonstration."""
        demo_buildings = [
            {
                "id": "bldg-3d-001",
                "parcel_id": "P-101",
                "name": "Coimbatore Municipal Complex",
                "height_m": 24.5,
                "base_elevation_m": 421.2,
                "floors": 7,
                "coordinates": [
                    [76.9550, 11.0165],
                    [76.9555, 11.0165],
                    [76.9555, 11.0170],
                    [76.9550, 11.0170],
                    [76.9550, 11.0165]
                ],
                "color": "#3B82F6"
            },
            {
                "id": "bldg-3d-002",
                "parcel_id": "P-102",
                "name": "Revenue Sub-Registrar Office",
                "height_m": 12.0,
                "base_elevation_m": 420.8,
                "floors": 3,
                "coordinates": [
                    [76.9560, 11.0172],
                    [76.9566, 11.0172],
                    [76.9566, 11.0178],
                    [76.9560, 11.0178],
                    [76.9560, 11.0172]
                ],
                "color": "#10B981"
            },
            {
                "id": "bldg-3d-003",
                "parcel_id": "P-103",
                "name": "Commercial Plaza (Conflict Parcel)",
                "height_m": 36.0,
                "base_elevation_m": 422.0,
                "floors": 10,
                "coordinates": [
                    [76.9570, 11.0180],
                    [76.9578, 11.0180],
                    [76.9578, 11.0188],
                    [76.9570, 11.0188],
                    [76.9570, 11.0180]
                ],
                "color": "#EF4444"
            }
        ]
        return demo_buildings


cadastral_3d_service = Cadastral3DService()
