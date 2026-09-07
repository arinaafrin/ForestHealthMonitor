import uuid
from datetime import date
from unittest.mock import patch

from shapely.geometry import Polygon
from geoalchemy2.shape import from_shape

from src.api.health_check_service import run_full_forest_health_check
from src.db.models import ForestRegion
from src.db.session import open_new_session


def _make_test_region(db):
    square = Polygon([(-122.45, 37.75), (-122.44, 37.75), (-122.44, 37.76), (-122.45, 37.75)])
    region = ForestRegion(name=f"Pipeline Test {uuid.uuid4()}", border_shape=from_shape(square, srid=4326))
    db.add(region)
    db.flush()
    return region


@patch("src.api.health_check_service.fetch_average_light_readings")
def test_a_healthy_forest_reading_produces_a_healthy_status(mock_satellite_call):
    db = open_new_session()
    region = _make_test_region(db)

    # Pretend the satellite saw strong, healthy vegetation
    mock_satellite_call.return_value = {"blue": 0.05, "red": 0.04, "nir": 0.5, "swir1": 0.2, "swir2": 0.1}

    result = run_full_forest_health_check(
        db, region, date(2026, 6, 1), date(2026, 6, 30), max_cloud_percent=20.0
    )

    assert result["greenness_score"] > 0.6
    assert result["came_from_cache"] is False

    db.rollback()
    db.close()


@patch("src.api.health_check_service.fetch_average_light_readings")
def test_the_second_identical_request_comes_from_cache(mock_satellite_call):
    db = open_new_session()
    region = _make_test_region(db)
    mock_satellite_call.return_value = {"blue": 0.05, "red": 0.04, "nir": 0.5, "swir1": 0.2, "swir2": 0.1}

    first_result = run_full_forest_health_check(db, region, date(2026, 6, 1), date(2026, 6, 30), 20.0)
    second_result = run_full_forest_health_check(db, region, date(2026, 6, 1), date(2026, 6, 30), 20.0)

    assert first_result["came_from_cache"] is False
    assert second_result["came_from_cache"] is True
    # The satellite should only have been called once, not twice
    assert mock_satellite_call.call_count == 1

    db.rollback()
    db.close()