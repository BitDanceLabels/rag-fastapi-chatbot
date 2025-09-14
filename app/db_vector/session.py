from app.config import Config
from sqlmodel import create_engine, SQLModel, Session

database_url = Config.DATABASE_URL

engine = create_engine(database_url, future=True)

def vector_db_init():
    with engine.begin() as conn:
        conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
        SQLModel.metadata.create_all

def get_session():
    with Session(engine) as session:
        yield session
