from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import datetime
import re

ALLOWED_PRIORITIES = {"low", "medium", "high", "critical"}
ALLOWED = {"active", "completed", "reopened"}

class ColumnCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: Optional[str] = Field(None, description="Hex color e.g. #3B82F6")
    wip_limit: Optional[int] = Field(None, ge=1, description="Max active cards. if None means unlimited cards")

    @field_validator("name")
    @classmethod
    def strip_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Column name cannot be blank or whitespace only")
        return v

    @field_validator("color")
    @classmethod
    def validate_color(cls, v):
        if v is not None and not re.fullmatch(r"#[0-9A-Fa-f]{6}", v):
            raise ValueError("color must be a valid 6-digit hex color e.g. #3B82F6")
        return v

class ColumnUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = None
    wip_limit: Optional[int] = Field(None, ge=1)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Column name cannot be blank or whitespace only")
        return v

    @field_validator("color")
    @classmethod
    def validate_color(cls, v):
        if v is not None and not re.fullmatch(r"#[0-9A-Fa-f]{6}", v):
            raise ValueError("color must be a valid 6-digit hex color e.g. #3B82F6")
        return v

class ColumnOrderItem(BaseModel):
    column_id: int = Field(..., gt=0)
    order: int = Field(..., gt=0, description="New order must be positive")

class ColumnReorder(BaseModel):
    column_orders: List[ColumnOrderItem] = Field(..., min_length=1)

    @model_validator(mode="after")
    def no_duplicate_ids(self):
        ids = [item.column_id for item in self.column_orders]
        if len(ids) != len(set(ids)):
            raise ValueError("column_orders contains duplicate column_id values")
        orders = [item.order for item in self.column_orders]
        if len(orders) != len(set(orders)):
            raise ValueError("column_orders contains duplicate order values")
        return self

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
    priority: Optional[str] = Field("medium", description="low | medium | high | critical")
    assignee_id: Optional[int] = Field(None, gt=0)
    due_date: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Card title cannot be blank or whitespace only")
        return v

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
    assignee_id: Optional[int] = Field(None, gt=0)
    due_date: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Card title cannot be blank or whitespace only")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        if v is not None and v not in ALLOWED_PRIORITIES:
            raise ValueError(f"priority must be one of: {', '.join(sorted(ALLOWED_PRIORITIES))}")
        return v

class CardMove(BaseModel):
    column_id: int = Field(..., gt=0, description="Destination column id")
    order: float = Field(..., gt=0, description="Target order in destination column")

class CardOrderItem(BaseModel):
    card_id: int = Field(..., gt=0)
    order: float = Field(..., gt=0, description="New order must be positive")

class CardReorder(BaseModel):
    card_orders: List[CardOrderItem] = Field(..., min_length=1)

    @model_validator(mode="after")
    def no_duplicate_ids(self):
        ids = [item.card_id for item in self.card_orders]
        if len(ids) != len(set(ids)):
            raise ValueError("card_orders contains duplicate card_id values")
        orders = [item.order for item in self.card_orders]
        if len(orders) != len(set(orders)):
            raise ValueError("card_orders contains duplicate order values")
        return self

class CardRestoreRequest(BaseModel):
    column_id: int = Field(..., gt=0, description="Column to restore the card into")

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

class CardFilterParams(BaseModel):
    q: Optional[str] = Field(None, description="Title keyword search")
    assignee_id: Optional[int] = Field(None, gt=0, description="Filter by assignee ID")
    priority: Optional[str] = Field(None, description="Filter by priority")
    status: Optional[str] = Field(None, description="Filter by status")
    due_before: Optional[datetime] = Field(None)
    due_after:   Optional[datetime] = Field(None)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        if v is not None and v not in ALLOWED_PRIORITIES:
            raise ValueError(f"priority must be one of: {', '.join(sorted(ALLOWED_PRIORITIES))}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in ALLOWED:
            raise ValueError(f"status must be one of: {', '.join(sorted(ALLOWED))}")
        return v