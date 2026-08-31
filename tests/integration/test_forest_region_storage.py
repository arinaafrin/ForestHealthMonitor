import uuid
from datetime import datetime, timezone

import pytest
from shapely.geometry import Polygon
from geoalchemy2.shape import from_shape

from src.db.models import ForestRegion, SatelliteCheck
from src.db.session import open_new_session


@pytest.fixture
def db():
    """Opens a connection for one test, and cleans up after it finishes."""
    connection = open_new_session()
    yield connection
    connection.rollback()  
    connection.close()


def test_a_new_forest_region_can_be_saved_and_read_back(db):
    simple_square = Polygon([(-122.45, 37.75), (-122.44, 37.75), (-122.44, 37.76), (-122.45, 37.75)])
    unique_name = f"Test Grove {uuid.uuid4()}"

    region = ForestRegion(name=unique_name, border_shape=from_shape(simple_square, srid=4326))
    db.add(region)
    db.commit()

    found = db.query(ForestRegion).filter(ForestRegion.name == unique_name).first()
    assert found is not None
    assert found.name == unique_name


def test_a_satellite_check_can_be_linked_to_its_region(db):
    simple_square = Polygon([(-122.45, 37.75), (-122.44, 37.75), (-122.44, 37.76), (-122.45, 37.75)])
    region = ForestRegion(name=f"Linked Grove {uuid.uuid4()}", border_shape=from_shape(simple_square, srid=4326))
    db.add(region)
    db.flush() 

    check = SatelliteCheck(
        region_id=region.id,
        checked_on=datetime.now(timezone.utc),
        greenness_score=0.75,
    )
    db.add(check)
    db.commit()

    assert check.region.name == region.name