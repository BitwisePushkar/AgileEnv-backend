from sqlalchemy import Column, Integer, Text, String, DateTime, ForeignKey, Boolean, UniqueConstraint, Enum
from sqlalchemy.orm import relationship
from app.utils.dbUtil import Base
from datetime import datetime, timezone
import enum

class JoinPolicy(enum.Enum):
    INVITE_ONLY = "invite_only" 
    CODE_ONLY = "code_only"
    
class InviteStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    code = Column(String(8), unique=True, index=True, nullable=False)
    admin_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    join_policy = Column(Enum(JoinPolicy),default=JoinPolicy.INVITE_ONLY,nullable=False,)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc),)
    is_active = Column(Boolean, default=True)

    admin = relationship("User", foreign_keys=[admin_id], back_populates="owned_workspaces")
    workspace_members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    chatrooms = relationship("Chatroom", back_populates="workspace", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="workspace", cascade="all, delete-orphan")
    invites = relationship("WorkspaceInvite", back_populates="workspace", cascade="all, delete-orphan")

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

class WorkspaceInvite(Base):
    __tablename__ = "workspace_invites"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    invited_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(Enum(InviteStatus), default=InviteStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)

    workspace = relationship("Workspace", back_populates="invites")
    inviter = relationship("User", foreign_keys=[invited_by],back_populates="invited_users")

    __table_args__ = (UniqueConstraint("workspace_id", "email", name="uq_workspace_invite_email"),)