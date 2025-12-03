from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from decouple import config

db_url=config("DATABASE_URL")
engine=create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)