import os
from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.db.models import DatabaseBase

DATABASE_HOST = os.getenv('DATABASE_HOST', 'forest_database')  
DATABASE_PORT = os.getenv('DATABASE_PORT', '5432')
DATABASE_USER = os.getenv('POSTGRES_USER', 'forest')
DATABASE_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'forest')
DATABASE_NAME = os.getenv('POSTGRES_DB', 'forest_health')

DATABASE_URL = f"postgresql+psycopg2://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

database_engine  = create_engine(DATABASE_URL, pool_pre_ping=True)
open_new_session = sessionmaker(bind=database_engine, autoflush=False, autocommit=False) 

def init_db():
    DatabaseBase.metadata.create_all(bind=database_engine)

def get_database_connection() -> Generator[Session, None, None]:
    connection = open_new_session()
    try:
        yield connection
    finally:
        connection.close()
