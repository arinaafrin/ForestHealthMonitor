def _shape_to_geojson(border_shape) -> dict:
    """Converts database geometry to GeoJSON for satellite queries"""
    from geoalchemy2.shape import to_shape
    return to_shape(border_shape).__geo_interface__