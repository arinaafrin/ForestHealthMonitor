import uuid
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_server_health_check_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status" : "ok"}

def test_a_new_region_can_be_registered():
    unique_name = f"API Test Grove {uuid.uuid4()}"
    request_body = {
        "name": unique_name,
        "border_shape_geojson": {
            "type": "Polygon",
            "coordinates": [[[-122.45, 37.75], [-122.44, 37.75], [-122.44, 37.76], [-122.45, 37.75]]],
        },
    }
    response = client.post("/regions", json=request_body)
    assert response.status_code == 201
    assert response.json()["name"] == unique_name

def test_registering_the_same_name_twice_is_rejected():
    unique_name = f"Duplicate Grove {uuid.uuid4}"
    request_body = {
        "name": unique_name,
        "border_shape_geojson": {
            "type": "Polygon",
            "coordinates": [[[-122.45, 37.75], [-122.44, 37.75], [-122.44, 37.76], [-122.45, 37.75]]],
        }
    }

    client.post("/regions", json=request_body)
    second_try = client.post("/regions", json=request_body)
    assert second_try.status_code == 409

def test_a_broken_shape_is_rejected():
    request_body = {
        "name": f"Broken Grove {uuid.uuid4()}",
        "border_shape_geojson": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0]]]},
    }

    response = client.post("/regions", json=request_body)
    assert response.status_code == 422