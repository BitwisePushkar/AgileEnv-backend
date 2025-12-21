from pydantic import BaseModel,EmailStr,Field,field_validator
from typing import Optional,List
from datetime import datetime
import re

class WorkspaceCreate(BaseModel):
    name:str=Field(...,min_length=3,max_length=100)
    description:Optional[str]=None
    code:str=Field(...,description="security code(ABCd123 or A1B2C3D4)")

    @field_validator('code')
    @classmethod
    def validate(cls,v):
        if not re.fullmatch(r'[A-Za-z0-9]{8}',v):
            raise ValueError("should contain alphabets and number only")
        alpha=sum(c.isalpha() for c in v)
        num=sum(c.isdigit() for c in v)
        if alpha!=4 or num!=4:
            raise ValueError("must contain exactly 4 alphabets and 4 numbers")
        
class WorkspaceUpdate(BaseModel):
    name:Optional[str]=Field(None,min_length=3,max_length=100)
    description:Optional[str]=None
    is_active:Optional[bool]=None

class WorkspaceInvite(BaseModel):
    email:List[EmailStr]=Field(...,min_items=1)

class UserBasic(BaseModel):
    id:int
    email:str
    username:Optional[str]=None
    
    class Config:
        from_attributes=True

class MemberDetail(BaseModel):
    id:int
    email:str
    username:Optional[str]=None
    joined_at:datetime
    role:str
    
    class Config:
        from_attributes = True

class WorkspaceResponse(BaseModel):
    id:int
    name:str
    description:Optional[str]
    code:str
    admin_id:int
    created_at:datetime
    updated_at:datetime
    is_active:bool
    member_count:Optional[int]=None
    
    class Config:
        from_attributes = True

class WorkspaceWithMembers(WorkspaceResponse):
    admin: UserBasic
    members: List[UserBasic]