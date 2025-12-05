from pydantic import BaseModel,Field,EmailStr,field_validator
import re

class UserCreate(BaseModel):
    email:EmailStr=Field(...,example="hell12@gmail.com")
    password:str=Field(...,example="hell")
    password2: str=Field(...,example="hell123")
    username:str=Field(...,example="Hellboy")

    @field_validator('password')
    @classmethod
    def val_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r'[0-9]', v):
            raise ValueError("Password must contain at least one number.")
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', v):
            raise ValueError("Password must contain at least one special character.")
        return v
    
    @field_validator('password2')
    @classmethod
    def passwords(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v
    
class UserList(BaseModel):
    id: int
    email: EmailStr
    username: str
    
    class Config:
        from_attributes = True
