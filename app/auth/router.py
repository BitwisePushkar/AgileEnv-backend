from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.auth.schema import UserCreate,UserList
from app.auth.crud import user_exist,save_user
from app.utils.dbUtil import get_db
from passlib.context import CryptContext

router = APIRouter()

pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash_pwd(pwd:str)->str:
    return pwd_context.hash(pwd)

def verify_pass(plain_pass:str,hashed_pass:str)->bool:
    return pwd_context.verify(plain_pass,hashed_pass)

@router.post("/api/register", status_code=status.HTTP_201_CREATED)
def register(user:UserCreate,db:Session=Depends(get_db)):
    exist_user = user_exist(db, user.email)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Email already registered")
    pwd_hash = hash_pwd(user.password)
    db_user = save_user(user,db,pwd_hash)
    return {"message": "User registered successfully","user": {"id": db_user.id,"email": db_user.email,"username": db_user.username}}
