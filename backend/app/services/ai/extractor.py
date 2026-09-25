"""
AI Building Footprint Extractor for BHUMI-FUSION V2
Extracts building structures from high-resolution drone ortho-imagery (ORI)
using image segmentation / contour extraction inference adapter and returns vector geometries.
"""

from typing import Dict, List, Any, Tuple
from backend.app.schemas.canonical import CanonicalBuilding
from backend.app.services.ai.inference_adapter import inference_adapter

class BuildingExtractor:
    def __init__(self, model_version: str = "YOLO+SAM-BuildingExtractor-v1.0"):
        self.model_version = model_version

    def extract_buildings_from_drone_features(
        self,
        drone_features: List[Dict[str, Any]]
    ) -> Tuple[List[CanonicalBuilding], Dict[str, Any]]:
        """
        Processes drone imagery extractions and identifies structural building footprints.
        Generates canonical building polygons with confidence ratings and inference metadata.
        """
        raw_blds, meta = inference_adapter.run_building_inference(
            drone_features, model_name=self.model_version
        )
        
        buildings = []
        for b in raw_blds:
            buildings.append(CanonicalBuilding(
                building_id=b["building_id"],
                parcel_uid=b.get("parcel_uid"),
                survey_number=b.get("survey_number"),
                geometry_geojson=b["geometry_geojson"],
                area_m2=b["area_m2"],
                building_type=b["building_type"],
                confidence=b["confidence"],
                extraction_source=b["extraction_source"],
                model_version=b["model_version"]
            ))

        return buildings, meta

building_extractor = BuildingExtractor()
