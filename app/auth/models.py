from sqlalchemy import Column,Integer,String,DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime,timezone

Base=declarative_base()
class User(Base):
    __tablename__ = "users"
    id=Column("Id",Integer,primary_key=True)
    email=Column("Email",String(100),unique=True,nullable=False,index=True)
    password=Column("Password",String(255),nullable=False)
    username=Column("UserName",String(50))
    created_at=Column("created_at",DateTime,default=lambda:datetime.now(timezone.utc))
    is_active= Column("status",Boolean,default=True)

class TokenBlackList(Base):
    __tablename__="Blacklist"
    id=Column("Id",Integer,primary_key=True)
    token=Column("token",String(500),nullable=True)
    blacklisted_at=Column("blacklisted_at",DateTime,default=lambda:datetime.now(timezone.utc))

class OTP(Base):
    __tablename__ = "OTPs"
    id = Column("Id",Integer, primary_key=True)
    email = Column("Email",String(100),nullable = False, index= True)
    otp_code = Column("Otp_code",String(6),nullable = False)
    purpose = Column("Purpose",String(20),nullable = False)
    created_at = Column("Created_at",DateTime,nullable= False, default = lambda: datetime.now(timezone.utc))
    is_used = Column("Is_used",Boolean,default = False )
    expires_at= Column("Expires_at",DateTime, nullable = False )

