from pydantic import BaseModel,field_validator,ValidationInfo
from typing import List,Optional
from datetime import datetime

class User(BaseModel):
    id:int
    username:str
    photo:Optional[str]=None
    class Config:
        from_attributes = True

class Message(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id:int
    chat_id:int
    sender_id:int
    name:str
    photo:Optional[str]=None
    content:str
    deleted:bool
    created_at:datetime
    updated_at:datetime
    class Config:
        from_attributes = True

class ChatroomBase(BaseModel):
    name:Optional[str]=None
    chat_type:str
    workspace_id:int

class ChatroomCreate(ChatroomBase):
    member_ids: List[int]
    
    @field_validator('chat_type')
    @classmethod
    def validate(cls,v):
        if v not in ['direct','group']:
            raise ValueError('Must be either "direct" or "group"')
        return v
    
    @field_validator('member_ids')
    @classmethod
    def validate_id(cls,v:List[int],info:ValidationInfo)->List[int]:
        chat_type = info.data.get('chat_type')
        if chat_type == 'direct' and len(v) != 1:
            raise ValueError('Direct chat must have exactly 1 other member')
        if chat_type == 'group' and len(v) < 2:
            raise ValueError('Group chat must have at least 2 members')
        return v

class ChatroomResponse(ChatroomBase):
    id:int
    created_by:Optional[int]
    created_at:datetime
    updated_at:datetime
    
    class Config:
        from_attributes = True