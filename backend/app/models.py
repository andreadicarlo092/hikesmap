from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict, Literal


# ---------------------------------------------------------------------------
# GeoJSON primitives
# ---------------------------------------------------------------------------

class PointGeometry(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: List[float]  # [lon, lat]


class LineStringGeometry(BaseModel):
    type: Literal["LineString"] = "LineString"
    coordinates: List[List[float]]  # [[lon, lat, alt?], ...]


# ---------------------------------------------------------------------------
# Trailhead models
# ---------------------------------------------------------------------------

class TrailheadProperties(BaseModel):
    id: int
    name: str
    trail_count: int


class TrailheadFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: PointGeometry
    properties: TrailheadProperties


class TrailheadCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: List[TrailheadFeature]


class TrailheadDetail(BaseModel):
    id: int
    name: str
    trail_count: int
    lat: float
    lon: float


# ---------------------------------------------------------------------------
# Trail models
# ---------------------------------------------------------------------------

class TrailSummary(BaseModel):
    id: int
    name: str
    cai_ref: Optional[str] = None
    difficulty: Optional[str] = None
    length_km: Optional[float] = None
    elevation_gain_m: Optional[int] = None
    elevation_loss_m: Optional[int] = None
    duration_hours: Optional[float] = None
    tags: Optional[List[str]] = None


class TrailProperties(BaseModel):
    id: int
    name: str
    cai_ref: Optional[str] = None
    difficulty: Optional[str] = None
    length_km: Optional[float] = None
    elevation_gain_m: Optional[int] = None
    elevation_loss_m: Optional[int] = None
    duration_hours: Optional[float] = None
    tags: Optional[List[str]] = None
    osm_url: Optional[str] = None


class TrailFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: LineStringGeometry
    properties: TrailProperties


# ---------------------------------------------------------------------------
# Elevation profile models
# ---------------------------------------------------------------------------

class ElevationSample(BaseModel):
    d_km: float
    alt_m: float


class ElevationProfile(BaseModel):
    profile: List[ElevationSample]
    gain_m: int
    loss_m: int
    max_alt_m: int
    min_alt_m: int
