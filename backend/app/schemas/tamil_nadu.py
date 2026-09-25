"""
Pydantic Schemas for Tamil Nadu Geospatial & Municipal Datasets
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class TamilNaduLayerMetadata(BaseModel):
    layer_id: str
    layer_name: str
    category: str  # Administrative, Civic, Infrastructure, Transportation, Education, Demographics
    geometry_type: str  # Point, LineString, Polygon
    feature_count: int
    format: str = "GeoJSON"
    crs: str = "EPSG:4326"
    source_agency: str
    description: str

class TamilNaduCatalogResponse(BaseModel):
    total_layers: int
    thematic_maps_count: int
    vector_layers_count: int
    infrastructure_tables_count: int
    layers: List[TamilNaduLayerMetadata]

class CoimbatoreRoadRecord(BaseModel):
    city_name: str
    zone_name: str
    ward_name: str
    ward_no: str
    total_length_km: str
    tar_roads_km: str
    concrete_roads_km: str
    footpath_both_sides_km: str
    footpath_one_side_km: str

class RoadInventoryResponse(BaseModel):
    city: str
    summary: Dict[str, Any]
    records: List[CoimbatoreRoadRecord]
    statewide_comparison: List[Dict[str, Any]]

class TamilNaduDistrictDemographics(BaseModel):
    district_code: str
    district_name: str
    headquarters: str
    total_population: int
    sc_population: int
    sc_percentage: float
    st_population: int
    st_percentage: float
    combined_sc_st_population: int
    combined_percentage: float
    literacy_rate: float
    taluks_count: int
