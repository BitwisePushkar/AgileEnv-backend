from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.auth.models import User, TokenBlackList, OTP, OAuthAccount, Profile
from app.auth.schemas import UserCreate
from datetime import datetime, timezone, timedelta
from random import randint
from typing import Optional
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

OTP_SEND_MAX = 5          
OTP_SEND_LOCK_MINUTES = 30  
OTP_VERIFY_LOCK_MINUTES = 10  

def user_exist(db: Session, email: str):
    return (db.query(User).filter(User.email == email, User.is_active == True, User.is_verified == True)
            .first())

def save_user(user: UserCreate, db: Session, hash_pwd: str):
    db_user = User(email=user.email,
                   password=hash_pwd,
                   username=user.username,
                   created_at=datetime.now(timezone.utc),
                   is_active=True, 
                   is_verified=True,)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def save_user_unverified(user: UserCreate, db: Session, hash_pwd: str):
    db_user = User(email=user.email,
                   password=hash_pwd,
                   username=user.username,
                   created_at=datetime.now(timezone.utc),
                   is_active=True,
                   is_verified=False,)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_unverified(db: Session, email: str, username: str, pwd: str):
    user = db.query(User).filter(User.email == email, User.is_verified == False).first()
    if user:
        user.username = username
        user.password = pwd
        user.created_at = datetime.now(timezone.utc)
        user.is_active = True
        db.commit()
        db.refresh(user)
        return user
    return None

def delete_otp_email(db: Session, email: str, purpose: str):
    deleted = db.query(OTP).filter(OTP.email == email, OTP.purpose == purpose).delete()
    db.commit()
    return deleted

def create_oauth_user(db: Session, email: str, username: str, provider: str, provider_user_id: str):
    original = username
    counter = 1
    while True:
        try:
            db_user = User(email=email,
                           password=None,
                           username=username,
                           created_at=datetime.now(timezone.utc),
                           is_active=True,
                           is_verified=True,)
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            oauth_account = OAuthAccount(user_id=db_user.id,
                                         provider=provider,
                                         provider_user_id=provider_user_id,
                                         created_at=datetime.now(timezone.utc),)
            db.add(oauth_account)
            db.commit()
            return db_user
        except IntegrityError as e:
            db.rollback()
            if "username" in str(e.orig).lower():
                username = f"{original}{counter}"
                counter += 1
                if counter > 100:
                    logger.error(f"Failed to generate unique username")
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Unable to generate unique username.",)
            else:
                logger.error(f"Unexpected IntegrityError during OAuth user creation: {e}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Account creation failed.",)


def get_user_oauth(db: Session, provider: str, provider_user_id: str):
    oauth_account = (db.query(OAuthAccount).filter(OAuthAccount.provider == provider, OAuthAccount.provider_user_id == provider_user_id)
                     .first())
    if oauth_account:
        return db.query(User).filter(User.id == oauth_account.user_id).first()
    return None

def link_oauth_account(db: Session, user_id: int, provider: str, provider_user_id: str):
    exist = (db.query(OAuthAccount).filter(OAuthAccount.user_id == user_id, OAuthAccount.provider == provider)
             .first())
    if exist:
        exist.provider_user_id = provider_user_id
        exist.updated_at = datetime.now(timezone.utc)
        db.commit()
        return exist
    oauth_account = OAuthAccount(user_id=user_id,
                                 provider=provider,
                                 provider_user_id=provider_user_id,
                                 created_at=datetime.now(timezone.utc),)
    db.add(oauth_account)
    db.commit()
    db.refresh(oauth_account)
    return oauth_account

def unlink_oauth_account(db: Session, user_id: int, provider: str):
    oauth_account = (db.query(OAuthAccount).filter(OAuthAccount.user_id == user_id, OAuthAccount.provider == provider)
                     .first())
    if oauth_account:
        db.delete(oauth_account)
        db.commit()
        return True
    return False

def get_user_oauth_account(db: Session, user_id: int):
    return db.query(OAuthAccount).filter(OAuthAccount.user_id == user_id).all()

def get_user_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_id(db: Session, id: int):
    return db.query(User).filter(User.id == id, User.is_active == True).first()

def get_user_and_username(db: Session, value: str):
    return db.query(User).filter((User.email == value) | (User.username == value)).first()

def get_all_user(db: Session):
    return db.query(User).filter(User.is_active == True).all()

def update_password(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.password = password
        db.commit()
        db.refresh(user)
    return user

def update_password_id(db: Session, id: int, password: str):
    user = db.query(User).filter(User.id == id).first()
    if user:
        user.password = password
        db.commit()
        db.refresh(user)
    return user

def deactivate_user(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.is_active = False
        db.commit()
        db.refresh(user)
    return user

def reactivate_user(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.is_active = True
        db.commit()
        db.refresh(user)
    return user

def delete_user(db: Session, id: int):
    user = db.query(User).filter(User.id == id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False

def verify_email(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.is_verified = True
        db.commit()
        db.refresh(user)
    return user

def add_token_blacklist(db: Session, token: str):
    db_token = TokenBlackList(token=token, blacklisted_at=datetime.now(timezone.utc))
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token

def token_blacklisted(db: Session, token: str) -> bool:
    result = db.query(TokenBlackList).filter(TokenBlackList.token == token).first()
    return result is not None

def clear_blacklist(db: Session, days: int = 30):
    expiry = datetime.now(timezone.utc) - timedelta(days=days)
    deleted = db.query(TokenBlackList).filter(TokenBlackList.blacklisted_at < expiry).delete()
    db.commit()
    return deleted

def is_otp_locked(db: Session, email: str, purpose: str) -> tuple:
    locked = (db.query(OTP).filter(OTP.email == email, OTP.purpose == purpose, OTP.locked_until.isnot(None),
                                   OTP.locked_until > datetime.now(timezone.utc),).first())
    if locked:
        remaining = locked.locked_until - datetime.now(timezone.utc)
        remaining_minutes = max(0, int(remaining.total_seconds() / 60))
        return (True, remaining_minutes)
    return (False, 0)

def is_otp_send_locked(db: Session, email: str, purpose: str) -> tuple:
    record = (db.query(OTP).filter(OTP.email == email, OTP.purpose == purpose, OTP.send_locked_until.isnot(None),
                                   OTP.send_locked_until > datetime.now(timezone.utc),).first())
    if record:
        remaining = record.send_locked_until - datetime.now(timezone.utc)
        remaining_minutes = max(0, int(remaining.total_seconds() / 60))
        return (True, remaining_minutes)
    return (False, 0)

def create_otp(db: Session, email: str, purpose: str):
    send_locked, send_remaining = is_otp_send_locked(db, email, purpose)
    if send_locked:
        return None
    verify_locked, _ = is_otp_locked(db, email, purpose)
    if verify_locked:
        return None
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    existing = db.query(OTP).filter(OTP.email == email, OTP.purpose == purpose).first()
    new_send_count = (existing.send_count + 1) if existing else 1
    carried_failed_attempt = existing.failed_attempt if existing else 0
    carried_locked_until = existing.locked_until if existing else None
    new_send_locked_until = None
    if new_send_count >= OTP_SEND_MAX:
        new_send_locked_until = datetime.now(timezone.utc) + timedelta(minutes=OTP_SEND_LOCK_MINUTES)
        logger.warning(f"OTP send limit reached for {email[:4]}*** purpose={purpose}")
    if existing:
        db.delete(existing)
        db.flush()
    otp_code = randint(100000, 999999)
    created_at = datetime.now(timezone.utc)
    expires_at = created_at + timedelta(minutes=10)
    db_otp = OTP(user_id=user.id,
                 email=email,
                 otp_code=str(otp_code),
                 purpose=purpose,
                 created_at=created_at,
                 expires_at=expires_at,
                 failed_attempt=carried_failed_attempt,
                 max_attempt=5,
                 locked_until=carried_locked_until,
                 send_count=new_send_count,
                 max_send_count=OTP_SEND_MAX,
                 send_locked_until=new_send_locked_until,)
    db.add(db_otp)
    db.commit()
    db.refresh(db_otp)
    return str(otp_code)

def verify_and_delete_otp(db: Session, email: str, otp: str, purpose: str):
    db.query(OTP).filter(OTP.expires_at < datetime.now(timezone.utc)).delete()
    db.commit()
    db_otp = (db.query(OTP).filter(OTP.email == email, OTP.purpose == purpose,
                                   OTP.expires_at >= datetime.now(timezone.utc),).first())
    if not db_otp:
        return (False, 0, "Invalid or expired OTP")
    if db_otp.otp_code == otp:
        db.delete(db_otp)
        db.commit()
        return (True, 0, None)
    db_otp.failed_attempt += 1
    if db_otp.failed_attempt >= db_otp.max_attempt:
        db_otp.locked_until = datetime.now(timezone.utc) + timedelta(minutes=OTP_VERIFY_LOCK_MINUTES)
        db.commit()
        db.refresh(db_otp)
        return (False, 0, f"Too many failed attempts. Try again in {OTP_VERIFY_LOCK_MINUTES} minutes.")
    db.commit()
    db.refresh(db_otp)
    remaining = db_otp.max_attempt - db_otp.failed_attempt
    return (False, remaining, f"Invalid OTP. {remaining} attempt(s) remaining.")

def get_profile_id(db: Session, id: int):
    return db.query(Profile).filter(Profile.user_id == id).first()

def create_profile(db: Session, id: int, data: dict):
    profile = Profile(user_id=id,
                      name=data.get("name"),
                      post=data.get("post"),
                      reason=data.get("reason"),
                      image_url=data.get("image_url"),
                      language=data.get("language", "en"),
                      created_at=datetime.now(timezone.utc),)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    logger.info(f"Profile created for user_id: {id}")
    return profile

def update_profile(db: Session, id: int, data: dict) -> Optional[Profile]:
    profile = get_profile_id(db, id)
    if not profile:
        return None
    if "name" in data:
        profile.name = data["name"]
    if "post" in data:
        profile.post = data["post"]
    if "reason" in data:
        profile.reason = data["reason"]
    if "image_url" in data:
        profile.image_url = data["image_url"]
    if "language" in data:
        profile.language = data["language"]
    profile.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(profile)
    logger.info(f"Profile updated for user_id: {id}")
    return profile

def get_profile(db: Session, id: int):
    profile = get_profile_id(db, id)
    user = db.query(User).filter(User.id == id).first()
    if not user:
        return None
    if not profile:
        return {"user_id": user.id,
                "name": None,
                "email": user.email,
                "username": user.username,
                "post": None,
                "reason": None,
                "image_url": None,
                "language": "en",}
    return {"user_id": profile.user_id,
            "name": profile.name,
            "email": user.email,
            "username": user.username,
            "post": profile.post,
            "reason": profile.reason,
            "image_url": profile.image_url,
            "language": profile.language or "en",}
