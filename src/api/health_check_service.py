import numpy as np
from datetime import datetime
from sqlalchemy.orm import Session

from src.cache.redis_client import build_cache_key, load_from_cache, save_to_cache
from src.db.models import ForestHealthStatus, ForestRegion, HealthAssessment, SatelliteCheck
from src.ingestion.earth_engine_client import fetch_average_light_readings
from src.processing.anomaly_detector import check_for_health_anomaly
from src.processing.vegetation_indices import summarize_all_health_indices

_SEVERITY_TO_STATUS = {
    "none": ForestHealthStatus.HEALTHY,
    "moderate": ForestHealthStatus.MODERATE_STRESS,
    "severe": ForestHealthStatus.SEVERE_STRESS,
}

def get_past_greenness_scores(db: Session, region_id, how_many: int = 24) -> list[float]:
    """Pulls this region's own past greenness scores, most recent first."""
    rows = (
        db.query(SatelliteCheck.greenness_score)
        .filter(SatelliteCheck.region_id == region_id)
        .order_by(SatelliteCheck.checked_on.desc())
        .limit(how_many)
        .all()
    )
    return [row[0] for row in rows]


def run_full_forest_health_check(
    db: Session,
    region: ForestRegion,
    start_date,
    end_date,
    max_cloud_percent: float,
) -> dict:
    cache_key = build_cache_key("health_check", str(region.id), f"{start_date}_{end_date}")
    cached_answer = load_from_cache(cache_key)
    if cached_answer is not None:
        cached_answer["came_from_cache"] = True
        return cached_answer

    border_shape_geojson = _shape_to_geojson(region.border_shape)

    light_readings = fetch_average_light_readings(
        border_shape_geojson, start_date, end_date, max_cloud_percent
    )
    health_scores = summarize_all_health_indices(
        {name: np.array([[value]]) for name, value in light_readings.items()}
    )

    past_scores = get_past_greenness_scores(db, region.id)
    anomaly_result = check_for_health_anomaly(health_scores["greenness"], past_scores)
    final_status = _SEVERITY_TO_STATUS[anomaly_result.severity_level]

    saved_check = SatelliteCheck(
        region_id=region.id,
        checked_on=datetime.combine(end_date, datetime.min.time()),
        greenness_score=health_scores["greenness"],
        burn_severity_score=health_scores["burn_severity"],
        moisture_stress_score=health_scores["moisture_stress"],
        canopy_density_score=health_scores["canopy_density"],
    )
    db.add(saved_check)
    db.flush()

    db.add(
        HealthAssessment(
            satellite_check_id=saved_check.id,
            status=final_status,
            steps_away_from_normal=anomaly_result.how_many_steps_away,
        )
    )
    db.commit()

    answer = {
        "region_id": str(region.id),
        "status": final_status.value,
        "steps_away_from_normal": anomaly_result.how_many_steps_away,
        "greenness_score": health_scores["greenness"],
        "burn_severity_score": health_scores["burn_severity"],
        "moisture_stress_score": health_scores["moisture_stress"],
        "canopy_density_score": health_scores["canopy_density"],
        "checked_on": saved_check.checked_on,
        "came_from_cache": False,
    }
    save_to_cache(cache_key, answer)
    return answer


def _shape_to_geojson(border_shape) -> dict:
    """Converts database geometry to GeoJSON for satellite queries"""
    from geoalchemy2.shape import to_shape
    return to_shape(border_shape).__geo_interface__