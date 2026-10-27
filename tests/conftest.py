import pytest
from sqlalchemy.exc import OperationalError
from src.db.session import database_engine
from src.db.models import DatabaseBase

@pytest.fixture(scope="session", autouse=True)
def create_tables():
    try:
        DatabaseBase.metadata.create_all(bind=database_engine)
    except OperationalError:
        pass
    yield