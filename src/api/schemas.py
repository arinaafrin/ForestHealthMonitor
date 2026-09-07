from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class NewRegionRequest(BaseModel):
    name: str
    border_shape_geojson: dict = Field(
        ..., description="A GeoJSON Polygon shape, describing the forest border"
    )

class RegionResponse(BaseModel):
    id: UUID
    name: str
    added_on: datetime

    model_config = ConfigDict(from_attributes=True)

class HealthCheckRequest(BaseModel):
    start_date: date
    end_date: date
    max_cloud_percent: float = 20.0

class HealthCheckResponse(BaseModel):
    region_id: UUID
    status: str
    steps_away_from_normal: float
    greenness_score: float
    burn_severity_score: float
    moisture_stress_score: float
    canopy_density_score: float
    checked_on: datetime
    came_from_cache: bool = False

class HistoryPointResponse(BaseModel):
    checked_on: datetime
    greenness_score: float
    burn_severity_score: float
    moisture_stress_score: float
    canopy_density_score: float
    model_config = ConfigDict(from_attributes=True)