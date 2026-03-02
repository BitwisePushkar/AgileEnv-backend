from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime
import re

def _validate_code(v: str) -> str:
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

class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, example="Acme Engineering")
    description: Optional[str] = Field(None, max_length=500, example="Main engineering workspace")
    code: str = Field(...,description="8-character security code",example="ABcd1234",)

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        return _validate_code(v)

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
    
class WorkspaceSettingsUpdate(BaseModel):
    join_policy: Literal["invite_only", "code_only"] = Field(...,description=("invite_only = only invited emails can join (secure). "
                                                                              "code_only = anyone with the code can join (fast onboarding, use temporarily)."),)

class JoinWorkspace(BaseModel):
    code: str = Field(..., description="8-character workspace security code", example="ABcd1234")

class InviteRequest(BaseModel):
    emails: list[EmailStr] = Field(..., min_length=1, description="List of emails to invite (max 20)")

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

class WorkspaceMemberResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    admin_id: int
    is_active: bool
    join_policy: str           
    member_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WorkspaceAdminResponse(WorkspaceMemberResponse):
    code: str

    class Config:
        from_attributes = True

class WorkspaceWithMembers(WorkspaceAdminResponse):
    admin: UserBasic
    members: List[UserBasic]

class WorkspaceMemberWithMembers(WorkspaceMemberResponse):
    admin: UserBasic
    members: List[UserBasic]

class WorkspaceSettingsResponse(BaseModel):
    id: int
    name: str
    join_policy: str
    is_active: bool
    code: str  

    class Config:
        from_attributes = True

class RotateCodeResponse(BaseModel):
    message: str
    new_code: str
    workspace_id: int

class PaginatedWorkspaceResponse(BaseModel):
    total: int
    page: int
    page_size: int
    results: List[WorkspaceMemberResponse] 

class InviteResponse(BaseModel):
    message: str
    invited_existing: List[str] = [] 
    invited_new: List[str] = [] 
    already_members: List[str] = [] 

class UserSearchResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    name: Optional[str] = None
    post: Optional[str] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True