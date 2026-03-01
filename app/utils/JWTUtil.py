from datetime import timedelta, timezone, datetime
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.utils.dbUtil import get_db
from app.auth import crud
from app.utils.settings import settings
from app.utils.redisUtils import redis_client 

oauth_schema = OAuth2PasswordBearer(tokenUrl="/api/login")

def create_token(data: dict, expire_delta: timedelta = None):
    to_encode = data.copy()
    if expire_delta:
        expire = datetime.now(timezone.utc) + expire_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except ExpiredSignatureError:
        return None
    except JWTError:
        return None

class AuthContext:
    def __init__(self, user, token: str):
        self.user = user
        self.token = token

def get_auth_context(token: str = Depends(oauth_schema),db: Session = Depends(get_db),) -> AuthContext:
    redis_blacklist_key = f"blacklist:{token}"
    if redis_client.exists(redis_blacklist_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Token has been revoked",
                            headers={"WWW-Authenticate": "Bearer"},)
    if crud.token_blacklisted(db, token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Token has been revoked",
                            headers={"WWW-Authenticate": "Bearer"},)
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate credentials",
                            headers={"WWW-Authenticate": "Bearer"},)

    email: str = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate credentials",
                            headers={"WWW-Authenticate": "Bearer"},)
    user = crud.get_user_email(db, email)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate credentials",
                            headers={"WWW-Authenticate": "Bearer"},)
    return AuthContext(user=user, token=token)

def get_user(auth: AuthContext = Depends(get_auth_context)):
    return auth.user

def active_user(current=Depends(get_user)):
    if not current.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    return current