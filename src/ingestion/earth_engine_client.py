from datetime import date
import ee

_has_connected = False

# Our own short names, mapped to Sentinel-2 real band names
_BAND_NAME_MAP = {
    "blue": "B2",
    "red": "B4",
    "nir": "B8",
    "swir1": "B11",
    "swir2": "B12",
}

def connect_to_satellite_service(service_account_email: str, private_key_path: str) -> None:
    """ Logs in to Google Earth Engine, once per program run """
    global _has_connected
    if _has_connected:
        return
    credentials = ee.ServiceAccountCredentials(service_account_email, private_key_path)
    ee.Initialize(credentials)
    _has_connected = True


def fetch_average_light_readings(
    border_shape_geojson: dict,
    start_date: date,
    end_date: date,
    max_cloud_percent: float = 80.0,
) -> dict[str, float]:
    """
    Asks the satellite for light readings over one forest area, during one
    date range. Cloudy pictures are skipped, since clouds hide the forest
    and would give us a wrong reading.

    Returns one average number per light band, from 0 (no light) to 1 (full light).
    """
    area = ee.Geometry(border_shape_geojson)

    clear_pictures = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(area)
        .filterDate(str(start_date), str(end_date))
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud_percent))
    )

    combined_picture = clear_pictures.median()  # blends several clear pictures into one reliable one

    raw_readings = combined_picture.select(list(_BAND_NAME_MAP.values())).reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=area,
        scale=10,  # 10 meters per pixel
        maxPixels=1_000_000_000,
    ).getInfo()

    # Satellite values come out 10,000 times too large, so we scale them back down to 0-1
    return {
        our_name: (raw_readings.get(satellite_name, 0) or 0) / 10000.0
        for our_name, satellite_name in _BAND_NAME_MAP.items()
    }

def get_ndvi_tile_url(border_shape_geojson: dict, start_date, end_date, max_cloud_percent: float = 20.0) -> str:
    area = ee.Geometry(border_shape_geojson)
    image = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(area).filterDate(str(start_date), str(end_date))
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud_percent))
        .median().clip(area)
    )
    ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    vis_params = {"min": -0.2, "max": 0.8, "palette": ["red", "yellow", "green"]}
    map_id = ndvi.getMapId(vis_params)
    return map_id["tile_fetcher"].url_format   # an XYZ {z}/{x}/{y} tile URL template