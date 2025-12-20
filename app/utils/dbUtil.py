from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from functools import lru_cache
from app import config
from app.auth.models import Base

@lru_cache()
def get_settings():
    return config.Settings()

def pgsql_url():
    settings = get_settings()
    return (
        f"{settings.DB_CONNECTION}://"
        f"{settings.DB_USERNAME}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_DATABASE}"
    )

engine = create_engine(pgsql_url(),pool_pre_ping=True,)
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine,)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()