from sqlalchemy import Column,Integer,String,DateTime,Boolean,ForeignKey,UniqueConstraint,Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime,timezone
from app.utils.dbUtil import Base

class User(Base):
    __tablename__ = "users"
    id=Column(Integer,primary_key=True)
    email=Column(String(100),unique=True,nullable=False,index=True)
    password=Column(String(255),nullable=True)
    username=Column(String(50),unique=True,nullable=False,index=True)
    created_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    is_active=Column(Boolean,default=True)
    is_verified=Column(Boolean,default=False) 
    otps=relationship("OTP",backref="user",cascade="all, delete-orphan")
    oauth_accounts=relationship("OAuthAccount",back_populates="user",cascade="all, delete-orphan")
    owned_workspaces=relationship("Workspace",back_populates="admin",foreign_keys="[Workspace.admin_id]")
    workspace_members=relationship("WorkspaceMember",back_populates="user",cascade="all, delete-orphan")
    profile=relationship("Profile",back_populates="user",uselist=False,cascade="all, delete-orphan")

    @property
    def workspaces(self):
        return [member.workspace for member in self.workspace_members]

class OAuthAccount(Base):
    __tablename__="oauth_accounts"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False)
    provider=Column(String(50),nullable=False)
    provider_user_id=Column(String(255),nullable=False)
    created_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    updated_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),
                      onupdate=lambda:datetime.now(timezone.utc))
    user=relationship("User",back_populates="oauth_accounts")
    __table_args__=(UniqueConstraint('user_id','provider',name='uq_user_provider'),)

class TokenBlackList(Base):
    __tablename__ = "Blacklist"
    id = Column(Integer, primary_key=True)
    token = Column(String(500), nullable=False, index=True, unique=True) 
    blacklisted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

class OTP(Base):
    __tablename__ = "OTPs"
    id = Column(Integer, primary_key=True)
    user_id=Column(Integer,ForeignKey("users.id",ondelete="CASCADE"))
    email = Column(String(100),nullable = False, index= True)
    otp_code = Column(String(6),nullable = False)
    purpose = Column(String(20),nullable = False)
    created_at = Column(DateTime(timezone=True),nullable= False, default = lambda: datetime.now(timezone.utc))
    expires_at= Column(DateTime(timezone=True), nullable = False )
    failed_attempt=Column(Integer,default=0)
    max_attempt=Column(Integer,default=5)
    locked_until=Column(DateTime(timezone=True),nullable=True)

class Profile(Base):
    __tablename__="profiles"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("users.id",ondelete="CASCADE"),unique=True,nullable=False,index=True)
    name=Column(String(100),nullable=False)
    post=Column(String(100),nullable=False)
    reason=Column(Text,nullable=True)
    image_url=Column(String(500),nullable=True)
    created_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    updated_at=Column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda:datetime.now(timezone.utc))
    user = relationship("User", back_populates="profile")