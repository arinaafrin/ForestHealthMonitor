import pytest
from src.db.session import database_engine
from src.db.models import DatabaseBase

@pytest.fixture(scope="session", autouse=True)
def create_tables():
    DatabaseBase.metadata.create_all(bind=database_engine)
    yield