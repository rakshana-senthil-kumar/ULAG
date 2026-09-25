"""
Geodesic Coordinate Reference System & Geometry Projection Utilities for ULAG
Ensures all metric spatial calculations (area, distances, deviations, buffers, GNSS)
are performed in an appropriate projected Cartesian CRS (e.g. UTM Zone 43N/44N)
rather than geographic degrees (EPSG:4326).
"""

import math
from typing import Dict, List, Any, Tuple, Optional
from shapely.geometry import shape, mapping, Polygon, MultiPolygon, Point, LineString
from shapely.validation import make_valid
from shapely.ops import transform
import pyproj
from pyproj import Transformer

_TRANSFORMER_CACHE: Dict[Tuple[str, str], Transformer] = {}

def get_transformer(src_crs: str, target_crs: str) -> Transformer:
    """Returns a cached PyProj Transformer instance."""
    key = (src_crs.upper(), target_crs.upper())
    if key not in _TRANSFORMER_CACHE:
        _TRANSFORMER_CACHE[key] = Transformer.from_crs(src_crs, target_crs, always_xy=True)
    return _TRANSFORMER_CACHE[key]

def get_optimal_projected_crs(lon: float, lat: float) -> str:
    """
    Determines the correct Universal Transverse Mercator (UTM) Projected CRS
    based on geographic longitude and latitude.
    - Longitudes 72°E to 78°E (e.g. Coimbatore, Salem, Erode) -> EPSG:32643 (UTM Zone 43N)
    - Longitudes 78°E to 84°E (e.g. Chennai, Madurai, Tiruchirappalli) -> EPSG:32644 (UTM Zone 44N)
    """
    zone = int((lon + 180.0) / 6.0) + 1
    base = 32600 if lat >= 0 else 32700
    return f"EPSG:{base + zone}"

def get_projected_crs_for_geometry(geom: Any, default_crs: str = "EPSG:32643") -> str:
    """Extracts centroid from geometry in EPSG:4326 and determines optimal projected CRS."""
    try:
        c = geom.centroid
        return get_optimal_projected_crs(c.x, c.y)
    except Exception:
        return default_crs

def project_geometry(geom: Any, src_crs: str = "EPSG:4326", target_crs: str = "EPSG:32643") -> Any:
    """
    Reprojects a Shapely geometry from source CRS to target CRS using high-precision PyProj.
    Returns the projected Shapely geometry in meters.
    """
    if not src_crs or src_crs.upper() == target_crs.upper():
        return geom
    transformer = get_transformer(src_crs, target_crs)
    return transform(transformer.transform, geom)

def unproject_geometry(geom: Any, src_crs: str = "EPSG:32643", target_crs: str = "EPSG:4326") -> Any:
    """Reprojects a Shapely geometry from projected Cartesian meters back to geographic degrees."""
    if not src_crs or src_crs.upper() == target_crs.upper():
        return geom
    transformer = get_transformer(src_crs, target_crs)
    return transform(transformer.transform, geom)

def project_point(lon: float, lat: float, src_crs: str = "EPSG:4326", target_crs: str = "EPSG:32643") -> Tuple[float, float]:
    """Reprojects a single 2D point (x, y) into metric projected Cartesian coordinates."""
    if not src_crs or src_crs.upper() == target_crs.upper():
        return (lon, lat)
    transformer = get_transformer(src_crs, target_crs)
    return transformer.transform(lon, lat)

def validate_and_repair_geometry(geom: Any, feature_id: str = "unknown") -> Tuple[Any, bool, Optional[str]]:
    """
    Validates a Shapely geometry. If invalid (self-intersection, unclosed ring, etc.),
    safely repairs it using make_valid without aggressive simplification.
    Returns: (repaired_geom, was_repaired, repair_reason)
    """
    if geom is None or geom.is_empty:
        return geom, False, "Geometry is null or empty"

    if geom.is_valid:
        return geom, False, None

    # Invalid geometry: attempt safe repair
    try:
        repaired = make_valid(geom)
        # If make_valid creates a GeometryCollection or MultiPolygon, extract largest polygon
        if repaired.geom_type == "MultiPolygon":
            # Pick largest polygon by area
            repaired = max(repaired.geoms, key=lambda g: g.area)
            reason = "Untangled self-intersections and resolved multi-part geometry to primary polygon"
        elif repaired.geom_type == "GeometryCollection":
            polys = [g for g in repaired.geoms if g.geom_type in ("Polygon", "MultiPolygon")]
            if polys:
                repaired = max(polys, key=lambda g: g.area)
                reason = "Extracted valid polygonal component from GeometryCollection"
            else:
                return geom, False, "Failed to extract valid polygon from GeometryCollection"
        else:
            reason = "Repaired self-intersecting boundary vertices via GEOS make_valid"

        return repaired, True, reason
    except Exception as e:
        return geom, False, f"Repair failed: {str(e)}"
