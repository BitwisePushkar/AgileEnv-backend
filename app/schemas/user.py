from pydantic import BaseModel,Field,EmailStr,ConfigDict
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr

class UserResponse(BaseModel):
    id:int
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    email: Optional[str] = None