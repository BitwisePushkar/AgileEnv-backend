from sqlalchemy import (Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum, JSON,)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.utils.dbUtil import Base
import enum

class EpicStatus(enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class SprintStatus(enum.Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"

class IssueType(enum.Enum):
    STORY = "story"
    SUBTASK = "subtask"
    TASK = "task"
    BUG = "bug"

class IssueStatus(enum.Enum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"

class IssuePriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Epic(Base):
    __tablename__ = "scrum_epics"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  
    status = Column(Enum(EpicStatus), nullable=False, default=EpicStatus.PLANNED)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="scrum_epics")
    creator = relationship("User", foreign_keys=[created_by])
    issues = relationship("ScrumIssue", back_populates="epic", foreign_keys="[ScrumIssue.epic_id]",)

class Sprint(Base):
    __tablename__ = "scrum_sprints"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    goal = Column(Text, nullable=True)
    status = Column(Enum(SprintStatus), nullable=False, default=SprintStatus.PLANNING)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                         onupdate=lambda: datetime.now(timezone.utc))
    end_warning_sent = Column(Boolean, nullable=False, default=False)
    carried_over_count = Column(Integer, nullable=True)

    project = relationship("Project", back_populates="scrum_sprints")
    issues = relationship("ScrumIssue",back_populates="sprint",foreign_keys="[ScrumIssue.sprint_id]",)

class ScrumIssue(Base):
    __tablename__ = "scrum_issues"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id",      ondelete="CASCADE"),  nullable=False)
    epic_id = Column(Integer, ForeignKey("scrum_epics.id",   ondelete="SET NULL"), nullable=True)
    sprint_id = Column(Integer, ForeignKey("scrum_sprints.id", ondelete="SET NULL"), nullable=True)
    parent_id = Column(Integer, ForeignKey("scrum_issues.id",  ondelete="CASCADE"),  nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(Enum(IssueType), nullable=False)
    status = Column(Enum(IssueStatus), nullable=False, default=IssueStatus.BACKLOG)
    priority = Column(Enum(IssuePriority), nullable=False, default=IssuePriority.MEDIUM)
    story_points = Column(Integer, nullable=True)
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reporter_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    order = Column(Float, nullable=False, default=1000.0)
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc))
    reminders_sent = Column(JSON, nullable=False, default=list)

    project = relationship("Project", back_populates="scrum_issues")
    epic = relationship("Epic", back_populates="issues", foreign_keys=[epic_id])
    sprint = relationship("Sprint", back_populates="issues", foreign_keys=[sprint_id])
    assignee = relationship("User", foreign_keys=[assignee_id])
    reporter = relationship("User", foreign_keys=[reporter_id])
    subtasks = relationship("ScrumIssue", back_populates="parent", foreign_keys=[parent_id], cascade="all, delete-orphan",)
    parent = relationship("ScrumIssue", back_populates="subtasks", foreign_keys=[parent_id], remote_side="ScrumIssue.id",)
    comments = relationship("IssueComment", back_populates="issue", cascade="all, delete-orphan", order_by="IssueComment.created_at",)

class IssueComment(Base):
    __tablename__ = "scrum_issue_comments"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("scrum_issues.id", ondelete="CASCADE"),  nullable=False)
    author_id = Column(Integer, ForeignKey("users.id",        ondelete="SET NULL"), nullable=True)
    content = Column(Text, nullable=False)
    is_edited = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    issue = relationship("ScrumIssue",  back_populates="comments")
    author = relationship("User", foreign_keys=[author_id])