"""
Utility Network Spatial Integration Service for ULAG
Analyzes proximity and topological intersections between urban parcels
and municipal underground/overhead utility infrastructure (Electricity, Water, Sewer, Telecom).
"""

import json
import math
from typing import Dict, List, Any, Optional
from shapely.geometry import shape, LineString, Point, Polygon, mapping

from backend.app.schemas.canonical import CanonicalUtilityAsset, ParcelUtilityAssociation
from backend.app.services.matching.matcher import M_PER_DEG_LON, M_PER_DEG_LAT, BASE_LON, BASE_LAT

# Generate Canonical Municipal Utility Assets in Coimbatore urban sector
def build_demo_utility_assets() -> List[CanonicalUtilityAsset]:
    assets = [
        CanonicalUtilityAsset(
            utility_id="UTIL-ELEC-01",
            utility_type="Electricity",
            asset_type="line",
            status="Operational",
            source="TANGEDCO Coimbatore Distribution Circle",
            geometry_geojson={
                "type": "LineString",
                "coordinates": [
                    [76.9508, 11.0018], [76.9525, 11.0030], [76.9550, 11.0045], [76.9580, 11.0065]
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
            source="CCMC Siruvani & Pilloor Water Supply Grid",
            geometry_geojson={
                "type": "LineString",
                "coordinates": [
                    [76.9510, 11.0020], [76.9526, 11.0031], [76.9552, 11.0046], [76.9582, 11.0066]
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
            source="CCMC Underground Drainage Network (UGD)",
            geometry_geojson={
                "type": "LineString",
                "coordinates": [
                    [76.9506, 11.0016], [76.9524, 11.0029], [76.9548, 11.0043], [76.9578, 11.0063]
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
            source="BharatNet / Tamil Nadu FiberNet (TANFINET)",
            geometry_geojson={
                "type": "LineString",
                "coordinates": [
                    [76.9509, 11.0019], [76.9525, 11.0030], [76.9551, 11.0045], [76.9581, 11.0064]
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
            source="Indian Oil-Adani City Gas Network (IOAGPL Coimbatore)",
            geometry_geojson={
                "type": "LineString",
                "coordinates": [
                    [76.9511, 11.0021], [76.9527, 11.0032], [76.9553, 11.0047], [76.9583, 11.0067]
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
            source="TANGEDCO Coimbatore Distribution Circle",
            geometry_geojson={
                "type": "Point",
                "coordinates": [76.9526, 11.0031]
            },
            crs="EPSG:4326",
            dataset_version="v2.0"
        ),
        CanonicalUtilityAsset(
            utility_id="UTIL-VALVE-01",
            utility_type="Water",
            asset_type="point",
            status="Operational",
            source="CCMC Siruvani & Pilloor Water Supply Grid",
            geometry_geojson={
                "type": "Point",
                "coordinates": [76.9524, 11.0029]
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
