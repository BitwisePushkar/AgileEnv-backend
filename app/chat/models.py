from sqlalchemy import (Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Enum, 
                        UniqueConstraint, Index,)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.utils.dbUtil import Base
import enum

class Chattype(enum.Enum):
    DIRECT = "direct"
    GROUP = "group"

class MessageType(enum.Enum):
    TEXT  = "text"
    IMAGE = "image"
    FILE  = "file"
    AUDIO = "audio"
    VIDEO = "video"

class Chatroom(Base):
    __tablename__ = "chatrooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)         
    chat_type = Column(Enum(Chattype), nullable=False)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    last_message_id = Column(Integer, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    member_associated = relationship("ChatroomMember", back_populates="chatroom", cascade="all, delete-orphan",foreign_keys="ChatroomMember.chat_id")
    members = relationship("User", secondary="chatroom_members", viewonly=True)
    messages = relationship("Message", back_populates="chatroom", cascade="all, delete-orphan", foreign_keys="Message.chat_id")
    pinned_messages = relationship("PinnedMessage", back_populates="chatroom", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by],back_populates="created_chatrooms")
    workspace = relationship("Workspace", back_populates="chatrooms")
    last_message = relationship("Message", foreign_keys=[last_message_id], post_update=True)

class ChatroomMember(Base):
    __tablename__ = "chatroom_members"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chatrooms.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_read_message_id = Column(Integer, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True, index=True)

    chatroom = relationship("Chatroom", back_populates="member_associated", foreign_keys=[chat_id])
    user = relationship("User", back_populates="chatroom_memberships")

    __table_args__ = (UniqueConstraint("chat_id", "user_id", name="uq_chatroom_member"),
                      Index("ix_chatroom_members_chat_user", "chat_id", "user_id"),)

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chatrooms.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=True)
    message_type = Column(Enum(MessageType), nullable=False, default=MessageType.TEXT)
    file_url = Column(String(1024), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)  
    is_edited = Column(Boolean, default=False, nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)
    reply_to_id = Column(Integer, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    is_forwarded = Column(Boolean, default=False, nullable=False)
    forwarded_from_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    chatroom = relationship("Chatroom", back_populates="messages", foreign_keys=[chat_id])
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    reply_to = relationship("Message", foreign_keys=[reply_to_id], remote_side="Message.id")
    forwarded_from_user = relationship("User", foreign_keys=[forwarded_from_user_id],back_populates="forwarded_messages")
    
    __table_args__ = (Index("ix_messages_chat_id_id", "chat_id", "id"),)

class PinnedMessage(Base):
    __tablename__ = "pinned_messages"

    id = Column(Integer, primary_key=True, index=True)
    chatroom_id = Column(Integer, ForeignKey("chatrooms.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    pinned_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    pinned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    chatroom = relationship("Chatroom", back_populates="pinned_messages")
    message = relationship("Message", foreign_keys=[message_id])
    pinner = relationship("User", foreign_keys=[pinned_by])

    __table_args__ = (UniqueConstraint("chatroom_id", "message_id", name="uq_pinned_message"),
                      Index("ix_pinned_messages_chatroom", "chatroom_id", "pinned_at"),)