from unittest.mock import MagicMock, patch
from src.ingestion.earth_engine_client import fetch_average_light_readings


@patch("src.ingestion.earth_engine_client.ee")
def test_light_readings_are_scaled_down_correctly(mock_earth_engine):
    # Pretend the satellite returned raw, oversized numbers
    fake_raw_values = {"B2": 450, "B4": 380, "B8": 4120, "B11": 1870, "B12": 910}

    mock_image_collection = MagicMock()
    mock_earth_engine.ImageCollection.return_value = mock_image_collection
    mock_image_collection.filterBounds.return_value = mock_image_collection
    mock_image_collection.filterDate.return_value = mock_image_collection
    mock_image_collection.filter.return_value = mock_image_collection
    mock_image_collection.median.return_value.select.return_value.reduceRegion.return_value.getInfo.return_value = fake_raw_values

    result = fetch_average_light_readings(
        border_shape_geojson={"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
        start_date="2026-06-01",
        end_date="2026-06-30",
    )

    # 4120 raw -> 0.412 real reflectance, and so on for each band
    assert result["nir"] == 0.412
    assert result["red"] == 0.038
    assert set(result.keys()) == {"blue", "red", "nir", "swir1", "swir2"}


@patch("src.ingestion.earth_engine_client.ee")
def test_missing_bands_do_not_crash_the_function(mock_earth_engine):
    # Pretend the satellite returned nothing at all (e.g. fully cloudy area)
    mock_image_collection = MagicMock()
    mock_earth_engine.ImageCollection.return_value = mock_image_collection
    mock_image_collection.filterBounds.return_value = mock_image_collection
    mock_image_collection.filterDate.return_value = mock_image_collection
    mock_image_collection.filter.return_value = mock_image_collection
    mock_image_collection.median.return_value.select.return_value.reduceRegion.return_value.getInfo.return_value = {}

    result = fetch_average_light_readings(
        border_shape_geojson={"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
        start_date="2026-06-01",
        end_date="2026-06-30",
    )

    assert result == {"blue": 0.0, "red": 0.0, "nir": 0.0, "swir1": 0.0, "swir2": 0.0}