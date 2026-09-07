import uuid
from datetime import datetime
from fastapi.testclient import TestClient
# from shapely.geometry import Polygon
# from geoalchemy2.shape import from_shape

from src.api.main import app
from src.db.models import ForestRegion, SatelliteCheck
from src.db.session import open_new_session

client = TestClient(app)


def _create_region_via_api():
    unique_name = f"History Test Grove {uuid.uuid4()}"
    request_body = {
        "name": unique_name,
        "border_shape_geojson": {
            "type": "Polygon",
            "coordinates": [[[-122.45, 37.75], [-122.44, 37.75], [-122.44, 37.76], [-122.45, 37.75]]],
        },
    }
    response = client.post("/regions", json=request_body)
    assert response.status_code == 201
    return response.json()["id"]


def _seed_satellite_check(db, region_id, checked_on, greenness_score):
    check = SatelliteCheck(
        region_id=region_id,
        checked_on=checked_on,
        greenness_score=greenness_score,
        burn_severity_score=0.1,
        moisture_stress_score=0.2,
        canopy_density_score=0.3,
    )
    db.add(check)
    db.commit()
    return check


def test_history_is_empty_for_a_region_with_no_checks_yet():
    region_id = _create_region_via_api()

    response = client.get(f"/regions/{region_id}/history")

    assert response.status_code == 200
    assert response.json() == []


def test_history_returns_all_checks_for_the_region():
    region_id = _create_region_via_api()
    db = open_new_session()

    _seed_satellite_check(db, region_id, datetime(2026, 5, 1), greenness_score=0.55)
    _seed_satellite_check(db, region_id, datetime(2026, 6, 1), greenness_score=0.40)
    db.close()

    response = client.get(f"/regions/{region_id}/history")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert {point["greenness_score"] for point in body} == {0.55, 0.40}


def test_history_is_ordered_oldest_to_newest():
    region_id = _create_region_via_api()
    db = open_new_session()

    _seed_satellite_check(db, region_id, datetime(2026, 6, 1), greenness_score=0.40)
    _seed_satellite_check(db, region_id, datetime(2026, 4, 1), greenness_score=0.60)
    _seed_satellite_check(db, region_id, datetime(2026, 5, 1), greenness_score=0.50)
    db.close()

    response = client.get(f"/regions/{region_id}/history")
    body = response.json()

    checked_on_dates = [point["checked_on"] for point in body]
    assert checked_on_dates == sorted(checked_on_dates)


def test_history_only_includes_checks_for_the_requested_region():
    region_a = _create_region_via_api()
    region_b = _create_region_via_api()
    db = open_new_session()

    _seed_satellite_check(db, region_a, datetime(2026, 6, 1), greenness_score=0.70)
    _seed_satellite_check(db, region_b, datetime(2026, 6, 1), greenness_score=0.10)
    db.close()

    response = client.get(f"/regions/{region_a}/history")
    body = response.json()

    assert len(body) == 1
    assert body[0]["greenness_score"] == 0.70


def test_history_for_a_nonexistent_region_returns_404():
    fake_region_id = uuid.uuid4()
    response = client.get(f"/regions/{fake_region_id}/history")

    assert response.status_code == 404