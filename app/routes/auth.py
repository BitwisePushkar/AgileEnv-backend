from fastapi import APIRouter, HTTPException,Depends
from app.schemas.user import UserCreate,UserResponse,UserUpdate
from app.models import auth
from app.models.auth import User
from app.database import SessionLocal, engine
from sqlalchemy.orm import Session
from typing import List

router = APIRouter()

auth.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
  
get_db()









@router.get("/",response_model=List[UserResponse])
def get_all_user(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.get("/{id}",response_model=UserResponse)
def get_user(id:int,db: Session = Depends(get_db)):
    user=db.query(User).filter(User.id==id).first()
    if not user:
        raise HTTPException(status_code=404,detail="user not found!")
    return user

@router.post("/",response_model=UserResponse)
def create_user(user:UserCreate,db: Session = Depends(get_db)):
    exist_user=db.query(User).filter(User.email==user.email).first()
    if exist_user:
        raise HTTPException(status_code=400,detail="user already exist!")
    new_user=User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.put("/{id}",response_model=UserResponse)
def reset_user(id:int,update: UserUpdate,db: Session = Depends(get_db)):
    user=db.query(User).filter(User.id==id).first()
    if not user:
        raise HTTPException(status_code=404,detail="user doesnt exist!")
    update = update.dict(exclude_unset=True)
    if "email" in update:
        raise HTTPException(status_code=400,detail="email cant be updated.")
    for field ,value in update.items():
        setattr(user,field,value)
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{id}")
def delete_user(id:int,db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}