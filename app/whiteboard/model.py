import enum
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.utils.dbUtil import Base

class ElementType(str, enum.Enum):
    PATH = "path"
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    LINE = "line"
    ARROW = "arrow"
    TEXT = "text"
    STICKY_NOTE = "sticky_note"
    IMAGE = "image"

class ActionType(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    MOVE = "move"
    RESIZE = "resize"
    DELETE = "delete"
    UNDO = "undo"

class Whiteboard(Base):
    __tablename__ = "whiteboards"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer,ForeignKey("projects.id", ondelete="CASCADE"), nullable=False,
                        unique=True, index=True,)
    title = Column(String(255), nullable=False, default="Whiteboard")
    is_locked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False,)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False,)

    project = relationship("Project", back_populates="whiteboard")
    elements = relationship("WhiteboardElement", back_populates="whiteboard", cascade="all, delete-orphan",)
    history_entries = relationship("WhiteboardHistory", back_populates="whiteboard", cascade="all, delete-orphan",)

    def __repr__(self) -> str:
        return f"<Whiteboard id={self.id} project_id={self.project_id}>"

class WhiteboardElement(Base):
    __tablename__ = "whiteboard_elements"

    id = Column(Integer, primary_key=True, index=True)
    whiteboard_id = Column(Integer, ForeignKey("whiteboards.id", ondelete="CASCADE"), nullable=False, index=True,)
    element_type = Column(Enum(ElementType), nullable=False)
    data = Column(JSONB, nullable=False)
    z_index = Column(Integer, nullable=False, default=0)
    is_locked = Column(Boolean, nullable=False, default=False)
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False,)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False,)

    whiteboard = relationship("Whiteboard", back_populates="elements")
    creator = relationship("User", foreign_keys=[created_by])
    last_editor = relationship("User", foreign_keys=[updated_by])
    history = relationship("WhiteboardHistory", back_populates="element", cascade="all, delete-orphan",)

    def __repr__(self) -> str:
        return f"<WhiteboardElement id={self.id} type={self.element_type}>"

class WhiteboardHistory(Base):
    __tablename__ = "whiteboard_history"

    id = Column(Integer, primary_key=True, index=True)
    whiteboard_id = Column(Integer, ForeignKey("whiteboards.id", ondelete="CASCADE"), nullable=False, index=True,)
    element_id = Column(Integer, ForeignKey("whiteboard_elements.id", ondelete="SET NULL"), nullable=True,  
                        index=True,)
    action_type = Column(Enum(ActionType), nullable=False)
    delta = Column(JSONB, nullable=False)
    performed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True,)
    performed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False,
                          index=True,  )

    whiteboard = relationship("Whiteboard", back_populates="history_entries")
    element = relationship("WhiteboardElement", back_populates="history")
    performer = relationship("User", foreign_keys=[performed_by])

    def __repr__(self) -> str:
        return f"<WhiteboardHistory id={self.id} action={self.action_type}>"