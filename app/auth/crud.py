from sqlalchemy.orm import Session
from app.auth.models import User,TokenBlackList,OTP,OAuthAccount
from app.auth.schemas import UserCreate
from datetime import datetime, timezone, timedelta
from random import randint

def user_exist(db: Session, email: str):
    return db.query(User).filter(User.email==email,User.is_active==True).first()

def save_user(user:UserCreate,db:Session,hash_pwd:str):
    db_user=User(email=user.email,password=hash_pwd,username=user.username,
                 created_at=datetime.now(timezone.utc),is_active=True,is_verified=True)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def save_user_unverified(user:UserCreate,db:Session,hash_pwd:str):
    db_user=User(email=user.email,password=hash_pwd,username=user.username,
                 created_at=datetime.now(timezone.utc),is_active=True,is_verified=False)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_oauth_user(db:Session,email:str,username:str,provider:str,provider_user_id:str):
    db_user=User(email=email,password=None,username=username,created_at=datetime.now(timezone.utc),
                 is_active=True,is_verified=True)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    oauth_account=OAuthAccount(user_id=db_user.id,provider=provider,provider_user_id=provider_user_id,
                               created_at=datetime.now(timezone.utc))
    db.add(oauth_account)
    db.commit()
    return db_user

def get_user_oauth(db:Session,provider:str,provider_user_id:str):
    oauth_account=db.query(OAuthAccount).filter(OAuthAccount.provider==provider,OAuthAccount.provider_user_id==provider_user_id).first()
    if oauth_account:
        return db.query(User).filter(User.id==oauth_account.user_id).first()
    return None

def link_oauth_account(db:Session,user_id:int,provider:str,provider_user_id:str):
    exist=db.query(OAuthAccount).filter(OAuthAccount.user_id==user_id,OAuthAccount.provider==provider).first()
    if exist:
        exist.provider_user_id=provider_user_id
        exist.updated_at=datetime.now(timezone.utc)
        db.commit()
        return exist
    oauth_account=OAuthAccount(user_id=user_id,provider=provider,provider_user_id=provider_user_id,
                               created_at=datetime.now(timezone.utc))
    db.add(oauth_account)
    db.commit()
    db.refresh(oauth_account)

    return oauth_account

def unlink_oauth_account(db:Session,user_id:int,provider:str):
    oauth_account=db.query(OAuthAccount).filter(OAuthAccount.user_id==user_id,OAuthAccount.provider==provider).first()
    if oauth_account:
        db.delete(oauth_account)
        db.commit()
        return True
    return False

def get_user_oauth_account(db:Session,user_id:int):
    return db.query(OAuthAccount).filter(OAuthAccount.user_id==user_id).all()

def get_user_email(db:Session,email:str):
    return db.query(User).filter(User.email==email).first()

def get_user_id(db:Session,id:int):
    return db.query(User).filter(User.id==id,User.is_active==True).first()

def get_user_and_username(db:Session,value:str):
    return db.query(User).filter((User.email==value)|(User.username==value)).first()

def get_all_user(db:Session):
    return db.query(User).filter(User.is_active==True).all()

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
        user.is_active=False
        db.commit()
        db.refresh(user)
    return user

def reactivate_user(db:Session,email:str):
    user=db.query(User).filter(User.email==email).first()
    if user:
        user.is_active=True
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

def verify_email(db:Session,email:str):
    user=db.query(User).filter(User.email==email).first()
    if user:
        user.is_verified=True
        db.commit()
        db.refresh(user)
    return user

def add_token_blacklist(db:Session,token:str):
    db_token=TokenBlackList(token=token,blacklisted_at=datetime.now(timezone.utc))
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token

def token_blacklisted(db:Session,token:str):
    result=db.query(TokenBlackList).filter(TokenBlackList.token==token).first()
    return result is not None

def clear_blacklist(db:Session,days:int=30):
    expiry=datetime.now(timezone.utc)-timedelta(days=days)
    delete=db.query(TokenBlackList).filter(TokenBlackList.blacklisted_at<expiry).delete()
    db.commit()
    return delete

def is_otp_locked(db:Session,email:str,purpose:str)->tuple:
    locked = db.query(OTP).filter(OTP.email==email,OTP.purpose==purpose,OTP.locked_until.isnot(None),
                                  OTP.locked_until>datetime.now(timezone.utc)).first()
    if locked:
        remaining=locked.locked_until-datetime.now(timezone.utc)
        remaining_minutes=max(0,int(remaining.total_seconds()/60))
        return (True,remaining_minutes)
    return (False,0)

def create_otp(db:Session,email:str,purpose:str):
    is_locked,remaining_minutes=is_otp_locked(db,email,purpose)
    if is_locked:
        return None 
    otp_code  = randint(100000,999999)
    created_at = datetime.now(timezone.utc)
    expires_at = created_at + timedelta(minutes=10)

    db.query(OTP).filter(OTP.email==email,OTP.purpose==purpose).delete()

    db_otp = OTP(email=email,otp_code=str(otp_code),purpose=purpose,created_at=created_at,
                 expires_at=expires_at,failed_attempt=0,max_attempt=5,locked_until=None)
    db.add(db_otp)
    db.commit()
    db.refresh(db_otp)
    return str(otp_code)
   
def verify_and_delete_otp(db:Session,email:str,otp:str,purpose:str ):
    db.query(OTP).filter(OTP.expires_at<datetime.now(timezone.utc)).delete()
    db.commit()
    db_otp = db.query(OTP).filter(OTP.email==email,OTP.otp_code==otp,OTP.purpose==purpose,
                                  OTP.expires_at>=datetime.now(timezone.utc)).first()
    if not db_otp:
        return(False,0,"Invalid or expired OTP")
    if db_otp.otp_code==otp:
        db.delete(db_otp)
        db.commit()
        return (True,0,None)
    db_otp.failed_attempt+=1
    if db_otp.failed_attempt>=db_otp.max_attempt:
        db_otp.locked_until = datetime.now(timezone.utc) + timedelta(minutes=10)
        db.commit()
        db.refresh(db_otp)
        return (False,0,"no request until 30 min")
    db.commit()
    db.refresh(db_otp)
    remaining = db_otp.max_attempt-db_otp.failed_attempt
    return (False,remaining,f"Invalid OTP.")

def clean_expired_otps(db: Session):
    deleted=db.query(OTP).filter(OTP.expires_at<datetime.now(timezone.utc)).delete()
    db.commit()
    return deleted