from pydantic import BaseModel, field_validator, ValidationInfo, model_validator, Field
from typing import List, Optional
from datetime import datetime

class UserBasic(BaseModel):
    id: int
    username: str
    photo: Optional[str] = None

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    content: Optional[str] = None
    message_type: str = "text"
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    reply_to_id: Optional[int] = None

    @field_validator("message_type")
    @classmethod
    def validate_message_type(cls, v: str) -> str:
        allowed = {"text", "image", "file", "audio", "video"}
        if v not in allowed:
            raise ValueError(f"message_type must be one of: {', '.join(sorted(allowed))}")
        return v

    @model_validator(mode="after")
    def check_content_or_file(self) -> "MessageCreate":
        is_text = self.message_type == "text"
        if is_text and not (self.content and self.content.strip()):
            raise ValueError("content is required for text messages and cannot be blank")
        if not is_text and not self.file_url:
            raise ValueError("file_url is required for image / file / audio messages")
        return self

class MessageWS(BaseModel):
    content: str

class MessageUpdate(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content cannot be blank")
        return v
    
class ForwardRequest(BaseModel):
    source_message_id: int
    caption: Optional[str] = None

    @field_validator("caption")
    @classmethod
    def caption_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("caption cannot be blank — omit the field instead")
        return v.strip() if v else None

class ReplyBasic(BaseModel):
    id: int
    sender_id: int
    sender_name: str
    content: Optional[str] = None
    message_type: str = "text"

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    chat_id: int
    sender: UserBasic
    content: Optional[str] = None 
    message_type: str = "text"
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    is_edited: bool = False
    deleted: bool = False
    reply_to: Optional[ReplyBasic] = None
    is_forwarded: bool = False
    forwarded_from_user: Optional[UserBasic] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ChatroomBase(BaseModel):
    name: Optional[str] = None
    chat_type: str
    workspace_id: int

class ChatroomCreate(ChatroomBase):
    member_ids: List[int]

    @field_validator("chat_type")
    @classmethod
    def validate_chat_type(cls, v: str) -> str:
        if v not in {"direct", "group"}:
            raise ValueError('chat_type must be "direct" or "group"')
        return v

    @field_validator("member_ids")
    @classmethod
    def validate_member_ids(cls, v: List[int], info: ValidationInfo) -> List[int]:
        chat_type = info.data.get("chat_type")
        if chat_type is None:
            return v
        if len(v) != len(set(v)):
            raise ValueError("member_ids contains duplicate user IDs")
        if chat_type == "direct":
            if len(v) != 1:
                raise ValueError("Direct chat requires exactly 1 other member ID")
        if chat_type == "group":
            if len(v) < 1:
                raise ValueError("Group chat requires at least 1 other member ID")
        return v

    @model_validator(mode="after")
    def group_requires_name(self) -> "ChatroomCreate":
        if self.chat_type == "group" and not (self.name and self.name.strip()):
            raise ValueError("name is required for group chats")
        return self

class ChatroomUpdate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name cannot be blank")
        if len(v) > 100:
            raise ValueError("name cannot exceed 100 characters")
        return v.strip()

class ChatroomResponse(ChatroomBase):
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    members: List[UserBasic] = []

    class Config:
        from_attributes = True

class ChatroomMemberResponse(BaseModel):
    id: int
    username: str
    photo: Optional[str] = None
    joined_at: datetime

    class Config:
        from_attributes = True

class UnreadCountResponse(BaseModel):
    chatroom_id: int
    unread_count: int

class PinnedMessageResponse(BaseModel):
    id: int        
    chatroom_id: int
    message: MessageResponse
    pinned_by: Optional[UserBasic] = None
    pinned_at: datetime

    class Config:
        from_attributes = True

class TransferOwnership(BaseModel):
    new_owner_id: int = Field(..., description="User ID of the member to make the new owner")