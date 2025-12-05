from sqlalchemy.orm import Session
from app.models import User
from app.auth.schema import UserCreate
from datetime import datetime, timezone, timedelta

def user_exist(db: Session, email: str):
    return db.query(User).filter(User.email == email,User.status == '1').first()

def save_user(user:UserCreate,db:Session,hash_pwd:str):
    db_user=User(email=user.email,password=hash_pwd,username=user.username,
                 created_at=datetime.now(timezone.utc),status='1')
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
