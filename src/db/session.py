from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = "postgresql+psycopg2://forest:forest@localhost:5432/forest_health"

database_engine  = create_engine(DATABASE_URL, pool_pre_ping=True)
open_new_session = sessionmaker(bind=database_engine, autoflush=False, autocommit=False) 


def get_database_connection() -> Generator[Session, None, None]:
    connection = open_new_session()

    try:
        yield connection
    finally:
        connection.close()
