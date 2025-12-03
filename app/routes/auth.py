from fastapi import APIRouter, HTTPException
from app.schemas import user
from app.models import auth
from app.database import SessionLocal, engine

router = APIRouter()

auth.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
  
get_db()

@router.get("/")
def get_user():
    pass

@router.post("/")
def create_user():
    pass
