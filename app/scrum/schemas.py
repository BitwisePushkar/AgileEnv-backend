from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import datetime, timedelta, timezone
import re

ALLOWED_EPIC_STATUSES = {"planned", "in_progress", "done"}
ALLOWED_ISSUE_TYPES = {"story", "subtask", "task", "bug"}
ALLOWED_ISSUE_STATUSES = {"backlog", "todo", "in_progress", "in_review", "done"}
ALLOWED_PRIORITIES = {"low", "medium", "high", "critical"}
NON_PARENT_TYPES = {"task", "bug", "subtask"}
EPIC_FORBIDDEN_TYPES = {"subtask"}
MAX_STORY_POINTS = 100
MAX_SPRINT_DAYS = 90
STATUS_TRANSITIONS: dict[str, set] = {
    "backlog": {"todo", "in_progress"},
    "todo": {"in_progress"},
    "in_progress": {"in_review", "done"},
    "in_review": {"in_progress", "done"},
    "done": {"in_progress"},
}

def _today_utc() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)

def _ensure_tz(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

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

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title cannot be blank")
        return v.strip()

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.fullmatch(r"#[0-9A-Fa-f]{6}", v):
            raise ValueError("color must be a valid 6-digit hex color e.g. #8B5CF6")
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> "EpicCreate":
        today = _today_utc()
        if self.end_date is not None and self.start_date is None:
            raise ValueError("start_date is required when end_date is provided")
        if self.start_date is not None:
            sd = _ensure_tz(self.start_date)
            if sd < today:
                raise ValueError("start_date cannot be in the past")
        if self.start_date is not None and self.end_date is not None:
            sd = _ensure_tz(self.start_date)
            ed = _ensure_tz(self.end_date)
            if ed <= sd:
                raise ValueError("end_date must be after start_date ")
        return self

class EpicUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.fullmatch(r"#[0-9A-Fa-f]{6}", v):
            raise ValueError("color must be a valid 6-digit hex color e.g. #8B5CF6")
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> "EpicUpdate":
        if self.start_date is not None and self.end_date is not None:
            sd = _ensure_tz(self.start_date)
            ed = _ensure_tz(self.end_date)
            if ed <= sd:
                raise ValueError("end_date must be after start_date ")
        return self

class EpicStatusUpdate(BaseModel):
    status: str = Field(..., description="planned | in_progress | done")

    @field_validator("status")
    @classmethod
    def validate(cls, v: str) -> str:
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

class EpicProgress(BaseModel):
    epic_id: int
    total_issues: int
    done_issues: int
    total_points: int
    done_points: int
    issue_progress: float = 0.0
    points_progress: float = 0.0

class SprintCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    goal: Optional[str] = None

class SprintUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    goal: Optional[str] = None

class SprintStart(BaseModel):
    start_date: datetime = Field(..., description="Sprint start — ISO 8601 with timezone")
    end_date: datetime = Field(..., description="Sprint end — ISO 8601, must be after start")

    @model_validator(mode="after")
    def validate_sprint_dates(self) -> "SprintStart":
        today = _today_utc()
        sd = _ensure_tz(self.start_date)
        ed = _ensure_tz(self.end_date)
        if sd < today:
            raise ValueError("start_date cannot be in the past")
        if ed <= sd:
            raise ValueError("end_date must be after start_date")
        duration = ed - sd
        if duration < timedelta(days=1):
            raise ValueError("Sprint must be at least 1 day long")
        if duration > timedelta(days=MAX_SPRINT_DAYS):
            raise ValueError("Sprint cannot be longer than {MAX_SPRINT_DAYS} days ")
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
    carried_over_count: Optional[int] = None

    class Config:
        from_attributes = True

class SprintDetailResponse(SprintResponse):
    issues: List["IssueResponse"] = []

class SprintStats(BaseModel):
    sprint_id: int
    sprint_name: str
    total: int
    todo: int
    in_progress: int
    in_review: int
    done: int
    total_points: int
    done_points: int
    completion_pct: float = 0.0

class IssueCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., description="story | subtask | task | bug")
    description: Optional[str] = None
    priority: Optional[str] = Field("medium", description="low | medium | high | critical")
    story_points: Optional[int] = Field(None, ge=0, le=MAX_STORY_POINTS,description=f"Estimate (0-{MAX_STORY_POINTS} points)")
    assignee_id: Optional[int] = None
    epic_id: Optional[int] = None
    parent_id: Optional[int] = None
    sprint_id: Optional[int] = None
    due_date: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title cannot be blank")
        return v.strip()

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ALLOWED_ISSUE_TYPES:
            raise ValueError(f"type must be one of: {', '.join(sorted(ALLOWED_ISSUE_TYPES))}")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_PRIORITIES:
            raise ValueError(f"priority must be one of: {', '.join(sorted(ALLOWED_PRIORITIES))}")
        return v

    @field_validator("due_date")
    @classmethod
    def due_date_not_in_past(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None:
            today = _today_utc()
            dv = _ensure_tz(v)
            if dv < today:
                raise ValueError("due_date cannot be in the past ")
        return v

    @model_validator(mode="after")
    def validate_type_rules(self) -> "IssueCreate":
        if self.type == "subtask":
            if not self.parent_id:
                raise ValueError("parent_id is required when type is 'subtask'")
            if self.epic_id is not None:
                raise ValueError("Subtasks cannot be assigned an epic directly the parent story's epic applies instead")
        if self.type != "subtask" and self.parent_id:
            raise ValueError("parent_id is only valid for type 'subtask'")
        return self

class IssueUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[str] = None
    story_points: Optional[int] = Field(None, ge=0, le=MAX_STORY_POINTS)
    assignee_id: Optional[int] = None
    epic_id: Optional[int] = None
    due_date: Optional[datetime] = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_PRIORITIES:
            raise ValueError(f"priority must be one of: {', '.join(sorted(ALLOWED_PRIORITIES))}")
        return v

    @field_validator("due_date")
    @classmethod
    def due_date_not_in_past(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None:
            today = _today_utc()
            dv = _ensure_tz(v)
            if dv < today:
                raise ValueError("due_date cannot be in the past ")
        return v

class IssueStatusUpdate(BaseModel):
    status: str = Field(..., description="backlog | todo | in_progress | in_review | done")

    @field_validator("status")
    @classmethod
    def validate(cls, v: str) -> str:
        if v not in ALLOWED_ISSUE_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(sorted(ALLOWED_ISSUE_STATUSES))}")
        return v

class IssueAssign(BaseModel):
    assignee_id: Optional[int] = Field(None, description="User ID to assign. Null to unassign.")

class IssuePoints(BaseModel):
    story_points: int = Field(..., ge=0, le=MAX_STORY_POINTS,description=f"Story point estimate (0–{MAX_STORY_POINTS})")

class IssueEpicUpdate(BaseModel):
    epic_id: Optional[int] = Field(None, description="Epic ID to link. Null to unlink.")

class IssueFilterParams(BaseModel):
    status: Optional[str] = Field(None, description="backlog | todo | in_progress | in_review | done")
    type: Optional[str] = Field(None, description="story | subtask | task | bug")
    priority: Optional[str] = Field(None, description="low | medium | high | critical")
    assignee_id: Optional[int] = Field(None, description="Filter by assignee user ID")
    epic_id: Optional[int] = Field(None, description="Filter by epic ID")
    sprint_id: Optional[int] = Field(None, description="Filter by sprint ID. Use 0 for backlog (no sprint).")
    search: Optional[str] = Field(None, max_length=200, description="Text search in title/description")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_ISSUE_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(sorted(ALLOWED_ISSUE_STATUSES))}")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_ISSUE_TYPES:
            raise ValueError(f"type must be one of: {', '.join(sorted(ALLOWED_ISSUE_TYPES))}")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_PRIORITIES:
            raise ValueError(f"priority must be one of: {', '.join(sorted(ALLOWED_PRIORITIES))}")
        return v

class BulkAddToSprint(BaseModel):
    issue_ids: List[int] = Field(..., min_length=1, max_length=50,description="List of issue IDs to add to the sprint")

class BulkAddResult(BaseModel):
    added: List[int]             
    skipped: List[int]             
    failed: List[dict]             

class BacklogReorderItem(BaseModel):
    issue_id: int
    order: float = Field(..., gt=0, le=1_000_000)

class BacklogReorder(BaseModel):
    items: List[BacklogReorderItem] = Field(..., min_length=1)

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
    content: str = Field(..., min_length=1, description="Updated comment text")

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
    carried_over_count: Optional[int] = None  

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