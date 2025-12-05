from sqlalchemy import Column,Integer,String,DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime,timezone

Base=declarative_base()
class User(Base):
    __tablename__ = "users"
    id=Column("Id",Integer,primary_key=True)
    email=Column("Email",String(100),unique=True,nullable=False)
    password=Column("Password",String(255),nullable=False)
    username=Column("UserName",String(50))
    created_at=Column("created_at",DateTime,default=lambda:datetime.now(timezone.utc))
    status= Column("status",String(1),default='1')