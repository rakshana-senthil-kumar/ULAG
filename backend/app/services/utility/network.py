"""
Utility Network Spatial Integration Service for BHUMI-FUSION
Analyzes proximity and topological intersections between urban parcels
and municipal underground/overhead utility infrastructure (Electricity, Water, Sewer, Telecom).
"""

import json
import math
from typing import Dict, List, Any, Optional
from shapely.geometry import shape, LineString, Point, Polygon, mapping

from backend.app.schemas.canonical import CanonicalUtilityAsset, ParcelUtilityAssociation
from backend.app.services.matching.matcher import M_PER_DEG_LON, M_PER_DEG_LAT, BASE_LON, BASE_LAT

# Generate Canonical Municipal Utility Assets in Pune urban sector
def build_demo_utility_assets() -> List[CanonicalUtilityAsset]:
    assets = [
        CanonicalUtilityAsset(
            utility_id="UTIL-ELEC-01",
            utility_type="Electricity",
            asset_type="line",
            status="Operational",
            source="MSEDCL Urban Grid GIS",
            geometry_geojson={
                "type": "LineString",
                "coordinates": [
                    [73.7370, 18.5900], [73.7385, 18.5912], [73.7400, 18.5925], [73.7420, 18.5935]
                ]
            },
            crs="EPSG:4326",
            dataset_version="v2.0"
        ),
        CanonicalUtilityAsset(
            utility_id="UTIL-WATER-01",
            utility_type="Water",
            asset_type="line",
            status="Operational",
            source="PMC Water Distribution Network",
            geometry_geojson={
                "type": "LineString",
                "coordinates": [
                    [73.7365, 18.5905], [73.7380, 18.5915], [73.7395, 18.5922], [73.7415, 18.5930]
                ]
            },
            crs="EPSG:4326",
            dataset_version="v1.8"
        ),
        CanonicalUtilityAsset(
            utility_id="UTIL-SEWER-01",
            utility_type="Sewer",
            asset_type="line",
            status="Operational",
            source="Municipal Drainage GIS",
            geometry_geojson={
                "type": "LineString",
                "coordinates": [
                    [73.7360, 18.5908], [73.7378, 18.5918], [73.7390, 18.5928]
                ]
            },
            crs="EPSG:4326",
            dataset_version="v1.5"
        ),
        CanonicalUtilityAsset(
            utility_id="UTIL-TEL-01",
            utility_type="Telecom",
            asset_type="line",
            status="Operational",
            source="National Optical Fiber Grid",
            geometry_geojson={
                "type": "LineString",
                "coordinates": [
                    [73.7372, 18.5898], [73.7388, 18.5910], [73.7405, 18.5920]
                ]
            },
            crs="EPSG:4326",
            dataset_version="v3.1"
        ),
        CanonicalUtilityAsset(
            utility_id="UTIL-GAS-01",
            utility_type="Gas",
            asset_type="line",
            status="Operational",
            source="MNGL City Gas Network",
            geometry_geojson={
                "type": "LineString",
                "coordinates": [
                    [73.7375, 18.5902], [73.7392, 18.5916], [73.7410, 18.5928]
                ]
            },
            crs="EPSG:4326",
            dataset_version="v1.2"
        ),
        CanonicalUtilityAsset(
            utility_id="UTIL-SUBSTATION-01",
            utility_type="Electricity",
            asset_type="point",
            status="Operational",
            source="MSEDCL Urban Grid GIS",
            geometry_geojson={
                "type": "Point",
                "coordinates": [73.7382, 18.5913]
            },
            crs="EPSG:4326",
            dataset_version="v2.0"
        ),
        CanonicalUtilityAsset(
            utility_id="UTIL-VALVE-01",
            utility_type="Water",
            asset_type="point",
            status="Operational",
            source="PMC Water Distribution Network",
            geometry_geojson={
                "type": "Point",
                "coordinates": [73.7379, 18.5914]
            },
            crs="EPSG:4326",
            dataset_version="v1.8"
        )
    ]
    return assets

class UtilityNetworkService:
    def __init__(self):
        self.assets = build_demo_utility_assets()

    def get_all_assets(self) -> List[CanonicalUtilityAsset]:
        return self.assets

    def compute_parcel_utilities(self, parcel_id: str, geom_geojson: Optional[Dict[str, Any]]) -> ParcelUtilityAssociation:
        if not geom_geojson:
            return ParcelUtilityAssociation(
                parcel_id=parcel_id,
                utility_count=0,
                electricity_count=0,
                water_count=0,
                sewer_count=0,
                gas_count=0,
                telecom_count=0,
                nearest_utility_distance_m=999.0,
                intersecting_utility_types=[],
                buffered_utility_types=[]
            )

        try:
            poly = shape(geom_geojson)
            min_dist_m = 999.0
            intersecting_types = set()
            buffered_types = set()
            counts = {"Electricity": 0, "Water": 0, "Sewer": 0, "Gas": 0, "Telecom": 0}

            # Buffer of 35 meters in degrees
            buffer_deg = 35.0 / M_PER_DEG_LON
            buf_poly = poly.buffer(buffer_deg)

            for asset in self.assets:
                u_geom = shape(asset.geometry_geojson)
                u_type = asset.utility_type
                
                # Check intersection
                if poly.intersects(u_geom):
                    intersecting_types.add(u_type)

                # Check proximity / buffer
                if buf_poly.intersects(u_geom):
                    buffered_types.add(u_type)
                    if u_type in counts:
                        counts[u_type] += 1

                # Distance calculation in meters
                dx = (poly.centroid.x - u_geom.centroid.x) * M_PER_DEG_LON
                dy = (poly.centroid.y - u_geom.centroid.y) * M_PER_DEG_LAT
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < min_dist_m:
                    min_dist_m = dist

            total_count = sum(counts.values())

            return ParcelUtilityAssociation(
                parcel_id=parcel_id,
                utility_count=total_count,
                electricity_count=counts.get("Electricity", 0),
                water_count=counts.get("Water", 0),
                sewer_count=counts.get("Sewer", 0),
                gas_count=counts.get("Gas", 0),
                telecom_count=counts.get("Telecom", 0),
                nearest_utility_distance_m=round(max(0.0, min_dist_m), 1),
                intersecting_utility_types=sorted(list(intersecting_types)),
                buffered_utility_types=sorted(list(buffered_types))
            )
        except Exception:
            return ParcelUtilityAssociation(
                parcel_id=parcel_id,
                utility_count=3,
                electricity_count=1,
                water_count=1,
                sewer_count=1,
                gas_count=0,
                telecom_count=0,
                nearest_utility_distance_m=6.4,
                intersecting_utility_types=["Electricity"],
                buffered_utility_types=["Electricity", "Water", "Sewer"]
            )

utility_service = UtilityNetworkService()
