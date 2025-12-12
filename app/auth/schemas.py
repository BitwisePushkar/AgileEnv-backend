from pydantic import BaseModel,Field,EmailStr,field_validator
from typing import Literal
import re

class UserCreate(BaseModel):
    email:EmailStr=Field(...,example="hell12@gmail.com")
    password:str=Field(...,example="hell123#")
    password2: str=Field(...,example="hell123#")
    username:str=Field(...,example="Hellboy")
    
    @field_validator('password')
    @classmethod
    def val_password(cls, v):
        if len(v) < 8 or len(v) > 50:
            raise ValueError("Password must be at least 8 characters and max 50 characters.")
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
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if len(v)<3 or len(v)>50:
            raise ValueError("Username must be 3-50 characters")
        if not re.match(r'^[a-zA-Z0-9_@]+$', v):
            raise ValueError("Username can only contain letters, numbers, underscores and @")
        if v[0].isdigit():
            raise ValueError("Username cannot start with a number")
        return v
    
class UserLogin(BaseModel):
    email:EmailStr=Field(...,example="hell12@gmail.com")
    password:str=Field(...,example="hell")

class EmailRequest(BaseModel):
    email:EmailStr=Field(...,example="hell12@gmail.com")
    
class PasswordResetRequest(BaseModel):
    email:str=Field(...,example="hell12@gmail.com")
    otp:str=Field(...,example="123456",min_length=6,max_length=6)
    @field_validator('otp')
    @classmethod
    def validate_otp(cls, v):
        if not v.isdigit():
            raise ValueError('OTP must contain only digits')
        if len(v) != 6:
            raise ValueError('OTP must be exactly 6 digits')
        return v
    
class PasswordResetToken(BaseModel):
    message:str
    reset_token:str
    expire_in:int=300
    
class PasswordResetComplete(BaseModel):
    reset_token:str=Field(...,example="abc123xyz")
    password:str=Field(...,example="hell123#")
    password2: str=Field(...,example="hell123#")

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
    
class Token(BaseModel):
    access_token:str
    refresh_token:str=None
    token_type:str="bearer"

class RefreshToken(BaseModel):
    refresh_token:str

class OTPRequest(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    purpose: str = Field(..., example="registration or password_reset")
    
    @field_validator('purpose')
    @classmethod
    def validate_purpose(cls, v):
        if v not in ['registration', 'password_reset']:
            raise ValueError('Purpose must be either "registration" or "password_reset"')
        return v

class OTPVerify(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    otp_code: str = Field(..., example="123456", min_length=6, max_length=6)
    purpose: str = Field(..., example="registration")
    
    @field_validator('otp_code')
    @classmethod
    def validate_otp(cls, v):
        if not v.isdigit():
            raise ValueError('OTP must contain only digits')
        if len(v) != 6:
            raise ValueError('OTP must be exactly 6 digits')
        return v
    
    @field_validator('purpose')
    @classmethod
    def validate_purpose(cls, v):
        if v not in ['registration', 'password_reset']:
            raise ValueError('Purpose must be either "registration" or "password_reset"')
        return v

class OTPResponse(BaseModel):
    message: str
    email: EmailStr
    
class GitHubAuthResponse(BaseModel):
    access_token:str
    refresh_token:str
    token_type:str="bearer"
    user:dict

class GitHubCallBack(BaseModel):
    code:str=Field(...,description="auth code by github")
    state:str=Field(...,description="protection state")

class OAuthLink(BaseModel):
    code:str=Field(...,description="auth code for oauth")

class GoogleAuthResponse(BaseModel):
    access_token:str
    refresh_token:str
    token_type:str="bearer"
    user:dict

class GoogleCallBack(BaseModel):
    code:str=Field(...,description="Authorization code from Google")
    state:str=Field(...,description="CSRF protection state")
