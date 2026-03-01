from sqlalchemy import Column, Integer, Text, String, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from app.utils.dbUtil import Base
from datetime import datetime, timezone

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    code = Column(String(8), unique=True, index=True, nullable=False)
    admin_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc),)
    is_active = Column(Boolean, default=True)

    admin = relationship("User", foreign_keys=[admin_id], back_populates="owned_workspaces")
    workspace_members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    chatrooms = relationship("Chatroom", back_populates="workspace", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="workspace", cascade="all, delete-orphan")

    @property
    def members(self):
        return [member.user for member in self.workspace_members]

    @property
    def member_count(self):
        return len(self.workspace_members)

class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    role = Column(String(50), default="member", nullable=False)

    workspace = relationship("Workspace", back_populates="workspace_members")
    user = relationship("User", back_populates="workspace_members")

    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),)