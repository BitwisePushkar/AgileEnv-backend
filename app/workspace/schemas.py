from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re

class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, example="Acme Engineering")
    description: Optional[str] = Field(None, max_length=500, example="Main engineering workspace")
    code: str = Field(...,description="8-character security code",example="ABcd1234",)

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9]{8}", v):
            raise ValueError("Code must be exactly 8 alphanumeric characters")
        uc = sum(c.isupper() for c in v)
        lc = sum(c.islower() for c in v)
        num = sum(c.isdigit() for c in v)
        if uc + lc != 4:
            raise ValueError("Code must contain exactly 4 letters")
        if num != 4:
            raise ValueError("Code must contain exactly 4 digits")
        if uc == 0:
            raise ValueError("Code must contain at least one uppercase letter")
        if lc == 0:
            raise ValueError("Code must contain at least one lowercase letter")
        if len(set(v)) < 6:
            raise ValueError("Code must contain at least 6 unique characters")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty or whitespace")
        return v

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Name cannot be empty or whitespace")
        return v

class JoinWorkspace(BaseModel):
    code: str = Field(..., description="8-character workspace security code", example="ABcd1234")

class WorkspaceInvite(BaseModel):
    emails: List[EmailStr] = Field(..., min_length=1, description="List of email addresses to invite")

class TransferOwnership(BaseModel):
    new_admin_id: int = Field(..., description="User ID of the member to promote as new admin")

class UpdateMemberRole(BaseModel):
    role: str = Field(..., description="Only 'member' is allowed here. Use /transfer/ to promote admin.")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"member"}
        if v not in allowed:
            raise ValueError("Role must be 'member'. To promote a member to admin, use the transfer ownership endpoint.")
        return v

class UserBasic(BaseModel):
    id: int
    email: str
    username: Optional[str] = None

    class Config:
        from_attributes = True

class MemberDetail(BaseModel):
    id: int
    email: str
    username: Optional[str] = None
    name: Optional[str] = None
    image_url: Optional[str] = None
    joined_at: datetime
    role: str

    class Config:
        from_attributes = True

class WorkspaceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    admin_id: int
    code: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    member_count: Optional[int] = None

    class Config:
        from_attributes = True

class WorkspaceWithMembers(WorkspaceResponse):
    admin: UserBasic
    members: List[UserBasic]

class UserSearchResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    name: Optional[str] = None
    post: Optional[str] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

class PaginatedWorkspaceResponse(BaseModel):
    total: int
    page: int
    page_size: int
    results: List[WorkspaceResponse]

class InviteResponse(BaseModel):
    message: str
    invited: List[str]      
    already_members: List[str]
    not_found: List[str]