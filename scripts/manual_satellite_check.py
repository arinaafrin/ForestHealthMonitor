import os
from datetime import date
from dotenv import load_dotenv
from src.ingestion.earth_engine_client import (
    connect_to_satellite_service,
    fetch_average_light_readings,
)

load_dotenv()

SERVICE_ACCOUNT_EMAIL = os.getenv("GEE_SERVICE_ACCOUNT_EMAIL")
PRIVATE_KEY_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials/gee-key.json")

connect_to_satellite_service(
    service_account_email=SERVICE_ACCOUNT_EMAIL,
    private_key_path=PRIVATE_KEY_PATH,
)

sample_geojson = {
    "type": "Polygon",
    "coordinates": [[
        [-122.45, 37.75],
        [-122.44, 37.75],
        [-122.44, 37.76],
        [-122.45, 37.76],
        [-122.45, 37.75]  
    ]],
}

readings = fetch_average_light_readings(
    border_shape_geojson=sample_geojson,
    start_date=date(2026, 6, 1),
    end_date=date(2026, 6, 30),
)

print("Real satellite readings:", readings)