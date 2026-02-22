from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re

ALLOWED_PRIORITIES = {"low", "medium", "high", "critical"}

class ColumnCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: Optional[str] = Field(None, description="Hex color e.g. #3B82F6")
    wip_limit: Optional[int] = Field(None, ge=1, description="None = unlimited")

    @field_validator("color")
    @classmethod
    def validate_color(cls, v):
        if v is not None and not re.fullmatch(r"#[0-9A-Fa-f]{6}", v):
            raise ValueError("color must be a valid hex color e.g. #3B82F6")
        return v

class ColumnUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = None
    wip_limit: Optional[int] = Field(None, ge=1)

    @field_validator("color")
    @classmethod
    def validate_color(cls, v):
        if v is not None and not re.fullmatch(r"#[0-9A-Fa-f]{6}", v):
            raise ValueError("color must be a valid hex color e.g. #3B82F6")
        return v

class ColumnReorder(BaseModel):
    column_orders: List[dict] = Field(..., description="[{column_id: int, order: int}]")

class ColumnResponse(BaseModel):
    id: int
    project_id: int
    name: str
    order: int
    color: Optional[str]
    wip_limit: Optional[int]
    is_done_column: bool = False
    card_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CardCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[str] = Field("medium", description="low, medium, high, critical")
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        if v is not None and v not in ALLOWED_PRIORITIES:
            raise ValueError(f"priority must be one of: {', '.join(sorted(ALLOWED_PRIORITIES))}")
        return v

class CardUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        if v is not None and v not in ALLOWED_PRIORITIES:
            raise ValueError(f"priority must be one of: {', '.join(sorted(ALLOWED_PRIORITIES))}")
        return v

class CardMove(BaseModel):
    column_id: int = Field(..., description="Destination column id")
    order: float = Field(..., description="Target float position in destination column")

class CardReorder(BaseModel):
    card_orders: List[dict] = Field(..., description="[{card_id: int, order: float}]")

class AssigneeBasic(BaseModel):
    id: int
    username: str
    photo: Optional[str] = None

    class Config:
        from_attributes = True

class CardResponse(BaseModel):
    id: int
    project_id: int
    column_id: Optional[int]
    title: str
    description: Optional[str]
    order: float
    priority: str
    assignee: Optional[AssigneeBasic] = None
    due_date: Optional[datetime]
    is_archived: bool
    status: str = "active"
    completed_at: Optional[datetime] = None
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ColumnWithCards(ColumnResponse):
    cards: List[CardResponse] = []

class BoardResponse(BaseModel):
    project_id: int
    board_type: str 
    columns: List[ColumnWithCards] = []
    total_cards: int = 0