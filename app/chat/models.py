from sqlalchemy import Column,Integer,String,Text,ForeignKey,DateTime,Boolean,Enum
from sqlalchemy.orm import relationship
from datetime import datetime,timezone
from app.utils.dbUtil import Base
import enum

class Chattype(enum.Enum):
    DIRECT="direct"
    GROUP="group"

class Chatroom(Base):
    __tablename__="chatrooms"
    id=Column(Integer,primary_key=True,index=True)
    name=Column(String(100),nullable=True)
    chat_type=Column(Enum(Chattype),nullable=False)
    workspace_id=Column(Integer,ForeignKey('workspaces.id',ondelete='CASCADE'),nullable=False)
    created_by=Column(Integer,ForeignKey('users.id',ondelete='SET NULL'),nullable=True)
    created_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    updated_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),
                      onupdate=lambda:datetime.now(timezone.utc))
    members=relationship('User',secondary='chatroom_members',back_populates='chatrooms')
    messages=relationship('Message',back_populates='chatroom',cascade='all, delete-orphan')
    creator=relationship('User',foreign_keys=[created_by])
    workspace = relationship('Workspace', back_populates='chatrooms')

class ChatroomMember(Base):
    __tablename__='chatroom_members'
    id=Column(Integer,primary_key=True,index=True)
    chat_id=Column(Integer,ForeignKey('chatrooms.id',ondelete='CASCADE'),nullable=False)
    user_id=Column(Integer,ForeignKey('users.id',ondelete='CASCADE'),nullable=False)
    joined_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    chatroom=relationship('Chatroom',backref='member_list')
    user=relationship('User',backref='chatroom_list')

class Message(Base):
    __tablename__ = 'messages'
    id=Column(Integer,primary_key=True,index=True)
    chat_id=Column(Integer,ForeignKey('chatrooms.id',ondelete='CASCADE'),nullable=False)
    sender_id=Column(Integer,ForeignKey('users.id',ondelete='CASCADE'),nullable=False)
    content=Column(Text,nullable=False)
    deleted=Column(Boolean,default=False)
    created_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),
                        onupdate=lambda:datetime.now(timezone.utc))
    chatroom=relationship('Chatroom',back_populates='messages')
    sender=relationship('User',foreign_keys=[sender_id])