from passlib.context import CryptContext

pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash_pwd(pwd:str)->str:
    return pwd_context.hash(pwd)

def verify_pass(plain_pass:str,hashed_pass:str)->bool:
    return pwd_context.verify(plain_pass,hashed_pass)