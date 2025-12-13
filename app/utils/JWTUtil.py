from functools import lru_cache
from app import config
from datetime import timedelta,timezone,datetime
from jose import JWTError,jwt
from jose.exceptions import ExpiredSignatureError
from fastapi import Depends,HTTPException,status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.utils.dbUtil import get_db
from app.auth import crud

@lru_cache()
def get_settings():
    return config.Settings()

settings = get_settings()
oauth_schema=OAuth2PasswordBearer(tokenUrl="/api/login")

def create_token(data:dict,expire_delta:timedelta=None):
    to_encode=data.copy()
    if expire_delta:
        expire=datetime.now(timezone.utc)+expire_delta
    else:
        expire=datetime.now(timezone.utc)+timedelta(days=settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp":expire,"iat":datetime.now(timezone.utc)})
    encode_jwt=jwt.encode(to_encode,settings.JWT_SECRET_KEY,algorithm=settings.JWT_ALGORITHM)
    return encode_jwt

def refresh_token(data:dict):
    to_encode=data.copy()
    expire=datetime.now(timezone.utc)+timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp":expire,"iat":datetime.now(timezone.utc),"type":"refresh"})
    encode_jwt=jwt.encode(to_encode,settings.JWT_SECRET_KEY,algorithm=settings.JWT_ALGORITHM)
    return encode_jwt

def decode_token(token:str):
    try:
        payload=jwt.decode(token,settings.JWT_SECRET_KEY,algorithms=[settings.JWT_ALGORITHM])
        return payload
    except ExpiredSignatureError:
        return None
    except JWTError:
        return None
    
def get_user(token:str=Depends(oauth_schema),db:Session=Depends(get_db)):
    if crud.token_blacklisted(db,token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="token revoked",headers={"WWW-Authenticate":"Bearer"})
    payload=decode_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="couldn't validate credentials",headers={"WWW-Authenticate":"Bearer"})
    email:str=payload.get("sub")
    if email is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="couldn't validate credentials",headers={"WWW-Authenticate":"Bearer"})
    user=crud.get_user_email(db,email)
    if user is None or user.is_active == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="couldn't validate credentials",headers={"WWW-Authenticate":"Bearer"})
    return user

def active_user(current=Depends(get_user)):
    if current.is_active == False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="invalid user")
    return current