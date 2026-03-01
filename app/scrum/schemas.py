from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import datetime
import re

ALLOWED_EPIC_STATUSES = {"planned", "in_progress", "done"}
ALLOWED_ISSUE_TYPES = {"story", "subtask", "task", "bug"}
ALLOWED_ISSUE_STATUSES = {"backlog", "todo", "in_progress", "in_review", "done"}
ALLOWED_PRIORITIES = {"low", "medium", "high", "critical"}
STATUS_TRANSITIONS = {"backlog": {"todo", "in_progress"},"todo": {"in_progress"},"in_progress": {"in_review", "done"},
                      "in_review": {"in_progress", "done"},"done": {"in_progress"},}
NON_PARENT_TYPES = {"task", "bug", "subtask"}

class UserBasic(BaseModel):
    id: int
    username: str
    photo: Optional[str] = None

    class Config:
        from_attributes = True

class EpicCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, description="Hex color e.g. #8B5CF6")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @field_validator("color")
    @classmethod
    def validate_color(cls, v):
        if v is not None and not re.fullmatch(r"#[0-9A-Fa-f]{6}", v):
            raise ValueError("color must be a valid hex color e.g. #8B5CF6")
        return v

    @model_validator(mode="after")
    def dates_must_be_valid(self):
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self

class EpicUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @field_validator("color")
    @classmethod
    def validate_color(cls, v):
        if v is not None and not re.fullmatch(r"#[0-9A-Fa-f]{6}", v):
            raise ValueError("color must be a valid hex color e.g. #8B5CF6")
        return v

    @model_validator(mode="after")
    def dates_must_be_valid(self):
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self

class EpicStatusUpdate(BaseModel):
    status: str = Field(..., description="planned | in_progress | done")

    @field_validator("status")
    @classmethod
    def validate(cls, v):
        if v not in ALLOWED_EPIC_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(sorted(ALLOWED_EPIC_STATUSES))}")
        return v

class EpicResponse(BaseModel):
    id: int
    project_id: int
    title: str
    description: Optional[str]
    color: Optional[str]
    status: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    issue_count: int = 0  

    class Config:
        from_attributes = True

class EpicDetailResponse(EpicResponse):
    issues: List["IssueResponse"] = []

class SprintCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    goal: Optional[str] = None

class SprintUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    goal: Optional[str] = None

class SprintStart(BaseModel):
    start_date: datetime = Field(..., description="Sprint start — ISO 8601")
    end_date:  datetime = Field(..., description="Sprint end — ISO 8601, must be after start")

    @model_validator(mode="after")
    def dates_must_be_valid(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self

class SprintResponse(BaseModel):
    id: int
    project_id: int
    name: str
    goal: Optional[str]
    status: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    issue_count: int = 0
    total_points: int = 0       

    class Config:
        from_attributes = True

class SprintDetailResponse(SprintResponse):
    issues: List["IssueResponse"] = []

class IssueCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., description="story | subtask | task | bug")
    description: Optional[str] = None
    priority: Optional[str] = Field("medium", description="low | medium | high | critical")
    story_points: Optional[int] = Field(None, ge=0)
    assignee_id: Optional[int] = None
    epic_id: Optional[int] = None    
    parent_id: Optional[int] = None    
    sprint_id: Optional[int] = None    
    due_date: Optional[datetime] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in ALLOWED_ISSUE_TYPES:
            raise ValueError(f"type must be one of: {', '.join(sorted(ALLOWED_ISSUE_TYPES))}")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        if v is not None and v not in ALLOWED_PRIORITIES:
            raise ValueError(f"priority must be one of: {', '.join(sorted(ALLOWED_PRIORITIES))}")
        return v

    @model_validator(mode="after")
    def validate_parent_rules(self):
        if self.type == "subtask" and not self.parent_id:
            raise ValueError("parent_id is required when type is 'subtask'")
        if self.type != "subtask" and self.parent_id:
            raise ValueError("parent_id is only allowed for type 'subtask'")
        return self

class IssueUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[str] = None
    story_points: Optional[int] = Field(None, ge=0)
    assignee_id: Optional[int] = None
    epic_id: Optional[int] = None
    due_date: Optional[datetime] = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        if v is not None and v not in ALLOWED_PRIORITIES:
            raise ValueError(f"priority must be one of: {', '.join(sorted(ALLOWED_PRIORITIES))}")
        return v

class IssueStatusUpdate(BaseModel):
    status: str = Field(..., description="backlog | todo | in_progress | in_review | done")

    @field_validator("status")
    @classmethod
    def validate(cls, v):
        if v not in ALLOWED_ISSUE_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(sorted(ALLOWED_ISSUE_STATUSES))}")
        return v

class IssueAssign(BaseModel):
    assignee_id: Optional[int] = Field(None, description="User id.")

class IssuePoints(BaseModel):
    story_points: int = Field(..., ge=0, description="Story point estimate.")

class IssueEpicUpdate(BaseModel):
    epic_id: Optional[int] = Field(None, description="Epic id.")

class IssueResponse(BaseModel):
    id: int
    project_id: int
    epic_id: Optional[int]
    sprint_id: Optional[int]
    parent_id: Optional[int]
    title: str
    description: Optional[str]
    type: str
    status: str
    priority: str
    story_points: Optional[int]
    effective_points: Optional[int] = None  
    assignee: Optional[UserBasic] = None
    reporter: Optional[UserBasic] = None
    order: float
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    subtask_count: int = 0
    comment_count: int = 0

    class Config:
        from_attributes = True

class IssueDetailResponse(IssueResponse):
    subtasks: List["IssueResponse"] = []
    comments: List["CommentResponse"] = []

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Comment text")

class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, description="Updated text")

class CommentResponse(BaseModel):
    id: int
    issue_id: int
    author: Optional[UserBasic]
    content: str
    is_edited: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BoardColumn(BaseModel):
    status: str
    issues: List[IssueResponse] = []
    issue_count: int = 0
    total_points: int = 0

class BoardResponse(BaseModel):
    project_id: int
    sprint_id: int
    sprint_name: str
    sprint_goal: Optional[str]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    total_points: int = 0
    done_points: int = 0
    columns: List[BoardColumn] = []

class BurndownDay(BaseModel):
    date: str     
    remaining: int      
    ideal: float   

class BurndownResponse(BaseModel):
    sprint_id: int
    sprint_name: str
    total_points: int
    days: List[BurndownDay] = []

class VelocityEntry(BaseModel):
    sprint_id: int
    sprint_name: str
    committed: int   
    completed: int   

class VelocityResponse(BaseModel):
    project_id: int
    average: float = 0.0
    sprints: List[VelocityEntry] = []

class ProjectSummary(BaseModel):
    project_id: int
    total_epics: int
    total_sprints: int
    active_sprint: Optional[SprintResponse]
    open_issues: int
    done_issues: int
    total_points: int
    done_points: int
    average_velocity: float

EpicDetailResponse.model_rebuild()
SprintDetailResponse.model_rebuild()
IssueDetailResponse.model_rebuild()