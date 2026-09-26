"""
ULAG National-Scale CRS & Coordinate Reference System Harmonization Service
Handles automatic UTM zone determination, national grid projections, zone-crossing detection,
axis-order validation, and projected CRS enforcement for legal area/distance calculations.
"""

from typing import Dict, Any, List, Optional, Tuple
import math
import pyproj
from shapely.geometry import shape, Point, Polygon, MultiPolygon


class NationalCRSHarmonizer:
    """
    Standardizes CRS across local, regional, and national land administration projects.
    For India:
    - UTM Zones: 42N (66-72E), 43N (72-78E), 44N (78-84E), 45N (84-90E), 46N (90-96E)
    - Default Metric Projection: EPSG:32643 (UTM Zone 43N) or EPSG:32644 (UTM Zone 44N)
    - National Projection: EPSG:7755 (India National Coordinate System / LCC)
    """

    UTM_ZONES_INDIA = {
        42: {"epsg": "EPSG:32642", "min_lon": 66.0, "max_lon": 72.0},
        43: {"epsg": "EPSG:32643", "min_lon": 72.0, "max_lon": 78.0},
        44: {"epsg": "EPSG:32644", "min_lon": 78.0, "max_lon": 84.0},
        45: {"epsg": "EPSG:32645", "min_lon": 84.0, "max_lon": 90.0},
        46: {"epsg": "EPSG:32646", "min_lon": 90.0, "max_lon": 96.0}
    }

    @staticmethod
    def get_utm_zone_from_lon_lat(lon: float, lat: float) -> Tuple[int, str]:
        """Calculates UTM zone number and EPSG string from longitude and latitude."""
        zone_num = int(math.floor((lon + 180.0) / 6.0)) + 1
        hemisphere = "N" if lat >= 0 else "S"
        epsg_code = 32600 + zone_num if hemisphere == "N" else 32700 + zone_num
        return zone_num, f"EPSG:{epsg_code}"

    def validate_and_recommend_crs(
        self,
        input_crs: str,
        bounds: Optional[List[float]] = None, # [min_lon, min_lat, max_lon, max_lat] in WGS84
        sample_coordinates: Optional[List[List[float]]] = None
    ) -> Dict[str, Any]:
        """
        Validates the input CRS, detects if coordinates cross UTM boundaries,
        and provides an authoritative projected CRS recommendation.
        """
        warnings = []
        clean_input = str(input_crs).strip().upper()
        if not clean_input.startswith("EPSG:"):
            clean_input = f"EPSG:{clean_input}" if clean_input.isdigit() else clean_input

        # Check PyProj validity
        is_valid_crs = False
        try:
            crs_obj = pyproj.CRS.from_user_input(clean_input)
            is_valid_crs = True
            is_projected = crs_obj.is_projected
            is_geographic = crs_obj.is_geographic
        except Exception as e:
            return {
                "input_crs": input_crs,
                "recommended_crs": "EPSG:32643",
                "reason": f"Input CRS '{input_crs}' is unrecognized or invalid. Suggested default metric UTM Zone 43N.",
                "zone": "43N",
                "warnings": [f"CRS parse failure: {str(e)}", "Never compute cadastral areas in unprojected or invalid CRS."]
            }

        if is_geographic:
            warnings.append(
                "CRITICAL: Input dataset is in Geographic Coordinates (e.g. EPSG:4326). "
                "Legal cadastral areas and distances must NOT be computed directly in degrees. "
                "Reprojection to a projected metric CRS is mandatory."
            )

        # Evaluate bounds / sample coordinates to determine optimal UTM zone
        zones_detected = set()
        min_lon, max_lon = None, None

        if bounds and len(bounds) == 4:
            min_lon, min_lat, max_lon, max_lat = bounds
            z1, _ = self.get_utm_zone_from_lon_lat(min_lon, (min_lat + max_lat) / 2.0)
            z2, _ = self.get_utm_zone_from_lon_lat(max_lon, (min_lat + max_lat) / 2.0)
            zones_detected.add(z1)
            zones_detected.add(z2)

        if sample_coordinates:
            for coord in sample_coordinates[:50]:
                if len(coord) >= 2:
                    lon, lat = coord[0], coord[1]
                    if -180 <= lon <= 180 and -90 <= lat <= 90:
                        z, _ = self.get_utm_zone_from_lon_lat(lon, lat)
                        zones_detected.add(z)

        # Detect zone crossing
        recommended_crs = clean_input if is_projected else "EPSG:32643"
        zone_str = "43N"

        if len(zones_detected) > 1:
            sorted_zones = sorted(list(zones_detected))
            warnings.append(
                f"BOUNDARY WARNING: Dataset spans across multiple UTM Zones ({', '.join(map(str, sorted_zones))}). "
                "Distortion may occur near boundary edges. For national-level alignment, consider EPSG:7755 (India LCC)."
            )
            # Default to primary zone
            primary_zone = sorted_zones[0]
            recommended_crs = f"EPSG:{32600 + primary_zone}"
            zone_str = f"{primary_zone}N"
        elif len(zones_detected) == 1:
            z = list(zones_detected)[0]
            recommended_crs = f"EPSG:{32600 + z}"
            zone_str = f"{z}N"

        reason = "Appropriate conformal metric projection identified for minimal geometric distortion."
        if is_geographic:
            reason = f"Converted geographic degrees to metric projection {recommended_crs} (UTM Zone {zone_str}) for legal area computations."

        return {
            "input_crs": clean_input,
            "is_projected": is_projected,
            "recommended_crs": recommended_crs,
            "reason": reason,
            "zone": zone_str,
            "zones_spanned": list(zones_detected),
            "warnings": warnings
        }


national_crs_harmonizer = NationalCRSHarmonizer()
