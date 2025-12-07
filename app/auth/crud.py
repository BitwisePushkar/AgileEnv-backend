from sqlalchemy.orm import Session
from app.auth.models import User,TokenBlackList, OTP
from app.auth.schemas import UserCreate
from datetime import datetime, timezone, timedelta
from random import randint


def user_exist(db: Session, email: str):
    return db.query(User).filter(User.email == email,User.status == '1').first()

def save_user(user:UserCreate,db:Session,hash_pwd:str):
    db_user=User(email=user.email,password=hash_pwd,username=user.username,
                 created_at=datetime.now(timezone.utc),status='1')
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_email(db:Session,email:str):
    return db.query(User).filter(User.email==email).first()

def get_user_id(db:Session,id:int):
    return db.query(User).filter(User.id==id,User.status=='1').first()

def get_user_and_username(db:Session,value:str):
    return db.query(User).filter((User.email==value)|(User.username==value)).first()

def get_all_user(db:Session):
    return db.query(User).filter(User.status=='1').all()

def update_password(db:Session,email:str,password:str):
    user=db.query(User).filter(User.email==email).first()
    if user:
        user.password=password
        db.commit()
        db.refresh(user)
    return user

def update_password_id(db:Session,id:int,password:str):
    user=db.query(User).filter(User.id==id).first()
    if user:
        user.password=password
        db.commit()
        db.refresh(user)
    return user

def deactivate_user(db:Session,email:str):
    user=db.query(User).filter(User.email==email).first()
    if user:
        user.status='0'
        db.commit()
        db.refresh(user)
    return user

def delete_user(db:Session,id:int):
    user=db.query(User).filter(User.id==id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False

def add_token_blacklist(db:Session,token:str):
    db_token=TokenBlackList(token=token,blacklisted_at=datetime.now(timezone.utc))
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token

def token_blacklisted(db:Session,token:str):
    result=db.query(TokenBlackList).filter(TokenBlackList.token==token).first()
    return result is not None


def create_otp(db:Session, email:str, purpose:str):
    otp_code  = randint(100000,999999)
    created_at = datetime.now(timezone.utc)
    expires_at = created_at + timedelta(minutes = 3)
    db_otp = OTP(email=email,
                 otp_code = str(otp_code),
                 purpose = purpose,
                 created_at = created_at,
                 expires_at = expires_at
                 )
    db.add(db_otp)
    db.commit()
    db.refresh(db_otp)

    return str(otp_code)
    
def verify_otp(db:Session, email:str, otp_code:str,purpose:str ):
    db_otp = db.query(OTP).filter(OTP.email == email,
                                  OTP.otp_code == otp_code,
                                  OTP.purpose == purpose).first()
    
    if not db_otp:
        return False
    if db_otp.is_used:
        return False 
    if db_otp.expires_at <= datetime.now(timezone.utc):
        return False
    return True
    

def mark_otp_as_used(db:Session, email:str,purpose:str,otp_code:str):
    db_otp = db.query(OTP).filter(OTP.email == email,
                                  OTP.otp_code == otp_code,
                                  OTP.purpose == purpose).first()
    if db_otp:
        db_otp.is_used=True
        db.add(db_otp)
        db.commit()
        db.refresh(db_otp)
        return True
    return False




    