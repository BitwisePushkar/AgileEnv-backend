from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re

ALLOWED_ROLES = {"viewer", "editor", "manager"}
ALLOWED_BOARD_TYPES = {"kanban", "scrum"}

class ProjectMemberBasic(BaseModel):
    id: int
    username: str
    photo: Optional[str] = None
    role: str

    class Config:
        from_attributes = True

class ProjectMemberDetail(BaseModel):
    id: int
    username: str
    email: str
    photo: Optional[str] = None
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=10)
    color: Optional[str] = Field(None, description="Hex color e.g. #3B82F6")
    board_type: str = Field(..., description="Board workflow type: 'kanban' or 'scrum'")

    @field_validator("board_type")
    @classmethod
    def validate_board_type(cls, v):
        if v not in ALLOWED_BOARD_TYPES:
            raise ValueError(f"board_type must be one of: {', '.join(sorted(ALLOWED_BOARD_TYPES))}")
        return v

    @field_validator("color")
    @classmethod
    def validate_color(cls, v):
        if v is not None and not re.fullmatch(r"#[0-9A-Fa-f]{6}", v):
            raise ValueError("color must be a valid hex color e.g. #3B82F6")
        return v

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=10)
    color: Optional[str] = Field(None)

    @field_validator("color")
    @classmethod
    def validate_color(cls, v):
        if v is not None and not re.fullmatch(r"#[0-9A-Fa-f]{6}", v):
            raise ValueError("color must be a valid hex color e.g. #3B82F6")
        return v

class UpdateProjectMemberRole(BaseModel):
    role: str = Field(..., description="New role: 'viewer', 'editor', or 'manager'")
    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in ALLOWED_ROLES:
            raise ValueError(f"role must be one of: {', '.join(sorted(ALLOWED_ROLES))}")
        return v

class ProjectResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: Optional[str]
    icon: Optional[str]
    color: Optional[str]
    board_type: str
    is_archived: bool
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    member_count: int = 0

    class Config:
        from_attributes = True

class ProjectDetailResponse(ProjectResponse):
    members: List[ProjectMemberBasic] = []