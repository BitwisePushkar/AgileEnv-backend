from sqlalchemy import (Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum,
                         UniqueConstraint, JSON,)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.utils.dbUtil import Base
import enum

class CardPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class CardStatus(enum.Enum):
    ACTIVE = "active"  
    COMPLETED = "completed"  
    REOPENED = "reopened"   

class KanbanColumn(Base):
    __tablename__ = "kanban_columns"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    order = Column(Integer, nullable=False, default=1000)
    color = Column(String(7), nullable=True)
    wip_limit = Column(Integer, nullable=True)
    is_done_column = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="kanban_columns")
    cards = relationship("KanbanCard", back_populates="column", cascade="all, delete-orphan", order_by="KanbanCard.order",)

    __table_args__ = (UniqueConstraint("project_id", "order", name="uq_kanban_column_order"),)

class KanbanCard(Base):
    __tablename__ = "kanban_cards"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"),  nullable=False)
    column_id = Column(Integer, ForeignKey("kanban_columns.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Float, nullable=False, default=1000.0)
    priority = Column(Enum(CardPriority), nullable=False, default=CardPriority.MEDIUM)
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    is_archived = Column(Boolean, default=False, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    status = Column(Enum(CardStatus), nullable=False, default=CardStatus.ACTIVE)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    reminders_sent = Column(JSON, nullable=False, default=list)

    column = relationship("KanbanColumn", back_populates="cards")
    project = relationship("Project", back_populates="kanban_cards")
    assignee = relationship("User", foreign_keys=[assignee_id])
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (UniqueConstraint("column_id", "order", name="uq_kanban_card_order"),)